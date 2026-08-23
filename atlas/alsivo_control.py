"""ALSIVO統合運用コントロール。"""
from __future__ import annotations

import json, os, re, shutil, subprocess, sys, tempfile, threading, webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, W, X, StringVar, Text, Tk, Toplevel
from tkinter import filedialog, messagebox
from tkinter import ttk
from typing import Any, Callable

BASE = Path(__file__).resolve().parent
REPO = BASE.parent
DATA = BASE / "data"
BLOG = REPO / "content" / "blog"
BLOG_IMAGES = REPO / "public" / "images" / "blog"
SOCIAL_IMAGES = REPO / "public" / "images" / "social"
ARTICLE_BACKUPS = BASE / "logs" / "deleted_content"
AFFILIATE_QUEUE = DATA / "affiliate_programs" / "human_approval_queue.json"
AFFILIATE_LINKS = DATA / "affiliate_links.json"
A8_EXPORTS = BASE / "exports"
LATEST_RUN = DATA / "automation" / "latest_run.json"
SITE = "https://www.alsivo.com"
STATUS_LABELS = {"approved_for_application":"申請予定","applied":"申請中","approved":"承認済み","rejected":"否認"}
STATUS_VALUES = {v:k for k,v in STATUS_LABELS.items()}

def load_json(path: Path, default: Any) -> Any:
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise RuntimeError(f"データを読み込めません: {path.name}") from error

def worker_python() -> str:
    executable=Path(sys.executable)
    if executable.name.lower()=="pythonw.exe":
        console_python=executable.with_name("python.exe")
        if console_python.is_file():return str(console_python)
    return str(executable)

def run_module(module: str, *args: str) -> str:
    result = subprocess.run([worker_python(),"-m",module,*args],cwd=BASE,capture_output=True,text=True,encoding="utf-8",errors="replace",check=False,env=utf8_environment())
    output = "\n".join(x.strip() for x in (result.stdout,result.stderr) if x.strip())
    if result.returncode: raise RuntimeError(output or "処理に失敗しました。")
    return output or "処理が完了しました。"

def run_git(*args: str, check: bool=True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git",*args],cwd=REPO,capture_output=True,text=True,encoding="utf-8",errors="replace",check=False,env=utf8_environment())
    if check and result.returncode: raise RuntimeError((result.stdout+"\n"+result.stderr).strip())
    return result

def utf8_environment() -> dict[str,str]:
    env=os.environ.copy(); env["PYTHONUTF8"]="1"; env["PYTHONIOENCODING"]="utf-8"; env["LANG"]="ja_JP.UTF-8"; return env

def title_of(path: Path) -> str:
    try: text=path.read_text(encoding="utf-8")[:5000]
    except OSError: return path.stem
    match=re.search(r'^title:\s*["\']?(.*?)["\']?\s*$',text,re.MULTILINE)
    return match.group(1).strip() if match else path.stem

class App:
    def __init__(self, root: Tk) -> None:
        self.root=root; root.title("ALSIVO 運用コントロール"); root.geometry("1160x750"); root.minsize(960,640)
        self.items: dict[str,dict[str,Any]]={}; self.status=StringVar(value="準備完了")
        style=ttk.Style(); style.configure("Title.TLabel",font=("Yu Gothic UI",18,"bold")); style.configure("Heading.TLabel",font=("Yu Gothic UI",11,"bold")); style.configure("Accent.TButton",font=("Yu Gothic UI",10,"bold"))
        head=ttk.Frame(root,padding=14); head.pack(fill=X); ttk.Label(head,text="ALSIVO 運用コントロール",style="Title.TLabel").pack(side=LEFT); ttk.Button(head,text="すべて更新",command=self.refresh).pack(side=RIGHT)
        self.tabs=ttk.Notebook(root); self.tabs.pack(fill=BOTH,expand=True,padx=14,pady=(0,10))
        self.build_articles(); self.build_affiliates(); self.build_automation()
        ttk.Label(root,textvariable=self.status,anchor=W).pack(fill=X,padx=16,pady=(0,10)); self.refresh()

    def build_articles(self) -> None:
        tab=ttk.Frame(self.tabs,padding=12); self.tabs.add(tab,text="記事の取り下げ")
        ttk.Label(tab,text="PC内の記事を表示しています。本番から取り下げる場合は、バックアップ後にGitHubへ削除を反映します。",foreground="#8a4300").pack(anchor=W,pady=(0,8))
        self.article_summary=ttk.Label(tab,style="Heading.TLabel"); self.article_summary.pack(anchor=W,pady=(0,8))
        self.article_tree=ttk.Treeview(tab,columns=("slug","title","state"),show="headings",selectmode="browse")
        for col,label,width in (("slug","記事ID",280),("title","記事タイトル",640),("state","Git状態",120)): self.article_tree.heading(col,text=label); self.article_tree.column(col,width=width,anchor="center" if col=="state" else W)
        self.article_tree.pack(fill=BOTH,expand=True)
        row=ttk.Frame(tab); row.pack(fill=X,pady=(10,0)); ttk.Button(row,text="記事をブラウザで確認",command=self.open_article).pack(side=LEFT); ttk.Button(row,text="選択記事を本番から取り下げ",command=self.remove_article).pack(side=RIGHT)

    def build_affiliates(self) -> None:
        tab=ttk.Frame(self.tabs,padding=12); self.tabs.add(tab,text="アフィリエイト案件")
        self.aff_summary=ttk.Label(tab,style="Heading.TLabel"); self.aff_summary.pack(anchor=W,pady=(0,8))
        ttk.Label(tab,text="申請予定：ASPでは未申請　｜　申請中：申請済み・審査待ち　｜　承認済み：広告掲載可能　｜　否認：審査不通過または提携不可",wraplength=1050).pack(anchor=W,pady=(0,10))
        toolbar=ttk.Frame(tab); toolbar.pack(fill=X,pady=(0,8)); ttk.Button(toolbar,text="新規案件を追加",style="Accent.TButton",command=self.add_dialog).pack(side=LEFT); ttk.Button(toolbar,text="CSVをインポート",command=self.import_affiliate_csv).pack(side=LEFT,padx=(8,0)); ttk.Button(toolbar,text="CSVフォーマットを作成",command=self.create_affiliate_template).pack(side=LEFT,padx=8); ttk.Button(toolbar,text="選択案件を削除",command=self.delete_affiliate).pack(side=LEFT); ttk.Button(toolbar,text="A8.net掲載URL CSVを作成",command=self.export_a8_csv).pack(side=RIGHT)
        body=ttk.Panedwindow(tab,orient="horizontal"); body.pack(fill=BOTH,expand=True); left=ttk.Frame(body); right=ttk.Frame(body,padding=(12,0,0,0)); body.add(left,weight=3); body.add(right,weight=2)
        self.aff_tree=ttk.Treeview(left,columns=("status","network","service"),show="headings",selectmode="browse")
        for col,label,width in (("status","状態",110),("network","ASP・運営元",150),("service","サービス",330)): self.aff_tree.heading(col,text=label); self.aff_tree.column(col,width=width,anchor="center" if col=="status" else W)
        self.aff_tree.pack(fill=BOTH,expand=True); self.aff_tree.bind("<<TreeviewSelect>>",self.show_affiliate)
        ttk.Label(right,text="案件情報",style="Heading.TLabel").pack(anchor=W); self.aff_detail=Text(right,wrap="word",height=10,font=("Yu Gothic UI",10),state="disabled"); self.aff_detail.pack(fill=BOTH,expand=True,pady=(6,10))
        form=ttk.Frame(right); form.pack(fill=X); self.aff_status=StringVar(value="申請中"); self.aff_program_id=StringVar(); self.aff_note=StringVar()
        ttk.Label(form,text="新しい状態").grid(row=0,column=0,sticky=W,pady=4); ttk.Combobox(form,textvariable=self.aff_status,values=tuple(STATUS_LABELS.values()),state="readonly").grid(row=0,column=1,sticky="ew",padx=(8,0),pady=4)
        ttk.Label(form,text="プログラムID").grid(row=1,column=0,sticky=W,pady=4); ttk.Entry(form,textvariable=self.aff_program_id).grid(row=1,column=1,sticky="ew",padx=(8,0),pady=4)
        ttk.Label(form,text="広告ソース").grid(row=2,column=0,sticky="nw",pady=4); self.aff_ad_source=Text(form,wrap="word",height=5,font=("Consolas",8)); self.aff_ad_source.grid(row=2,column=1,sticky="ew",padx=(8,0),pady=4)
        ttk.Label(form,text="PR内容・掲載条件").grid(row=3,column=0,sticky="nw",pady=4); self.aff_promotion=Text(form,wrap="word",height=4,font=("Yu Gothic UI",9)); self.aff_promotion.grid(row=3,column=1,sticky="ew",padx=(8,0),pady=4)
        ttk.Label(form,text="メモ").grid(row=4,column=0,sticky=W,pady=4); ttk.Entry(form,textvariable=self.aff_note).grid(row=4,column=1,sticky="ew",padx=(8,0),pady=4); form.columnconfigure(1,weight=1)
        ttk.Button(right,text="状態を保存",style="Accent.TButton",command=self.save_affiliate).pack(anchor="e",pady=(10,0))

    def build_automation(self) -> None:
        tab=ttk.Frame(self.tabs,padding=18); self.tabs.add(tab,text="記事自動公開")
        ttk.Label(tab,text="毎朝7時の自動運転",style="Title.TLabel").pack(anchor=W)
        ttk.Label(tab,text="Atlasが新記事・リライト・待機を判断します。記事を作成・更新した日は本番公開後にX・Instagramへ自動配信します。",wraplength=900).pack(anchor=W,pady=(6,16))
        box=ttk.LabelFrame(tab,text="直近の実行結果",padding=14); box.pack(fill=X); self.auto_text=ttk.Label(box,font=("Yu Gothic UI",11)); self.auto_text.pack(anchor=W)
        controls=ttk.LabelFrame(tab,text="手動実行",padding=14); controls.pack(fill=X,pady=(18,0)); ttk.Button(controls,text="安全確認（公開しない）",command=lambda:self.run_atlas("dry")).pack(side=LEFT); ttk.Button(controls,text="通常の自動運転を今すぐ実行",command=lambda:self.run_atlas("normal")).pack(side=LEFT,padx=10); ttk.Button(controls,text="新記事を1本作成・公開",style="Accent.TButton",command=lambda:self.run_atlas("new")).pack(side=LEFT); ttk.Button(controls,text="ALSIVOを開く",command=lambda:webbrowser.open(SITE)).pack(side=RIGHT)

    def refresh(self) -> None:
        try: self.refresh_articles(); self.refresh_affiliates(); self.refresh_automation(); self.status.set("最新データを表示しています。")
        except Exception as error: messagebox.showerror("読み込みエラー",str(error))

    def refresh_articles(self) -> None:
        files=sorted(BLOG.glob("*.mdx"),reverse=True); head={x.strip() for x in run_git("ls-tree","-r","--name-only","HEAD","--",":(top)content/blog").stdout.splitlines() if x.endswith(".mdx")}
        self.article_tree.delete(*self.article_tree.get_children()); committed=0
        for path in files:
            name=path.relative_to(REPO).as_posix(); exists=name in head; committed+=int(exists); self.article_tree.insert("",END,iid=path.stem,values=(path.stem,title_of(path),"公開経路" if exists else "ローカルのみ"))
        self.article_summary.config(text=f"PC内 {len(files)}件　Gitコミット済み {committed}件")

    def open_article(self) -> None:
        selected=self.article_tree.selection()
        if selected: webbrowser.open(f"{SITE}/blog/{selected[0]}")

    def remove_article(self) -> None:
        selected=self.article_tree.selection()
        if not selected: messagebox.showinfo("記事の取り下げ","対象記事を選択してください。"); return
        slug=selected[0]
        if not messagebox.askyesno("最終確認",f"「{slug}」を本番サイトから取り下げますか？\n\n削除前のファイルはPC内へバックアップします。"): return
        targets=[BLOG/f"{slug}.mdx",BLOG_IMAGES/f"{slug}.png",BLOG_IMAGES/f"{slug}.webp",SOCIAL_IMAGES/f"{slug}-instagram.png"]; existing=[p.resolve() for p in targets if p.exists()]; allowed={BLOG.resolve(),BLOG_IMAGES.resolve(),SOCIAL_IMAGES.resolve()}
        if not existing or any(p.parent not in allowed for p in existing): messagebox.showerror("安全確認エラー","対象を安全に特定できませんでした。"); return
        backup=ARTICLE_BACKUPS/datetime.now().strftime("%Y%m%d-%H%M%S")/slug; backup.mkdir(parents=True,exist_ok=False); rel=[]
        try:
            for path in existing: shutil.copy2(path,backup/path.name); rel.append(path.relative_to(REPO.resolve()).as_posix()); path.unlink()
            run_git("add","-A","--",*rel); diff=run_git("diff","--cached","--quiet","--",*rel,check=False)
            if diff.returncode==1: run_git("commit","-m",f"Remove ALSIVO article: {slug}","--",*rel); run_git("push","origin",run_git("branch","--show-current").stdout.strip())
        except Exception as error: messagebox.showerror("取り下げエラー",f"バックアップ: {backup}\n\n{error}"); self.refresh_articles(); return
        self.refresh_articles(); messagebox.showinfo("完了",f"記事を取り下げました。\nバックアップ: {backup}")

    def refresh_affiliates(self) -> None:
        data=load_json(AFFILIATE_QUEUE,{"programs":[]}); registry=load_json(AFFILIATE_LINKS,{}); programs=[x for x in data.get("programs",[]) if isinstance(x,dict)]; self.items={str(x.get("service","")):x for x in programs}; self.aff_tree.delete(*self.aff_tree.get_children()); counts={}
        for item in programs:
            service=str(item.get("service","")); current=str(item.get("approval_status","")); counts[current]=counts.get(current,0)+1; active=isinstance(registry,dict) and registry.get(service,{}).get("affiliate_status")=="active"; self.aff_tree.insert("",END,iid=service,values=("承認済み" if active else STATUS_LABELS.get(current,current),item.get("network",""),service))
        self.aff_summary.config(text=f"登録案件 {len(programs)}件　申請中 {counts.get('applied',0)}件　承認済み {counts.get('approved',0)}件　否認 {counts.get('rejected',0)}件")

    def selected_affiliate(self) -> dict[str,Any]|None:
        selected=self.aff_tree.selection(); return self.items.get(selected[0]) if selected else None

    def show_affiliate(self,_event:Any=None) -> None:
        item=self.selected_affiliate()
        if not item:return
        registry=load_json(AFFILIATE_LINKS,{}); registry_item=registry.get(str(item.get("service","")),{}); promotion=str(registry_item.get("promotion_details",item.get("promotion_details",""))); ad_source=str(registry_item.get("ad_source","")); text=f"記事で使うサービス名: {item.get('service','')}\nASP案件名（正式名称）: {item.get('program_name','')}\nASP・運営元: {item.get('network','')}\nプログラムID: {item.get('program_id','')}\n現在の状態: {STATUS_LABELS.get(str(item.get('approval_status','')),item.get('approval_status',''))}\n申請ページ: {item.get('program_url','')}\n\n広告ソース: {'登録済み' if ad_source else '未登録'}\n\nPR内容・掲載条件:\n{promotion}\n\nメモ:\n{item.get('human_notes','')}"; self.set_text(self.aff_detail,text); current=str(item.get("approval_status","applied")); self.aff_status.set(STATUS_LABELS.get(current,"申請中")); self.aff_note.set(str(item.get("human_notes",""))); self.set_text_value(self.aff_ad_source,ad_source); self.set_text_value(self.aff_promotion,promotion); self.aff_program_id.set(str(registry_item.get("program_id",item.get("program_id",""))))

    def save_affiliate(self) -> None:
        item=self.selected_affiliate()
        if not item:messagebox.showinfo("案件管理","対象案件を選択してください。");return
        status=STATUS_VALUES[self.aff_status.get()]; ad_source=self.aff_ad_source.get("1.0",END).strip()
        if status=="approved" and not ad_source:messagebox.showwarning("広告ソースが必要です","承認済みの場合はASPが発行した広告ソースを入力してください。");return
        program_id=self.aff_program_id.get().strip()
        if str(item.get("network","")).strip().lower()=="a8.net" and status=="approved" and not program_id:messagebox.showwarning("プログラムIDが必要です","A8.netの承認済み案件にはプログラムIDを入力してください。");return
        promotion=self.aff_promotion.get("1.0",END).strip(); args=["add","--service",str(item.get("service","")),"--program-name",str(item.get("program_name","")),"--network",str(item.get("network","")),"--program-url",str(item.get("program_url","")),"--program-id",program_id,"--commission",str(item.get("commission","")),"--promotion-details",promotion,"--status",status,"--ad-source",ad_source,"--notes",self.aff_note.get().strip()]; self.background("案件状態を更新中...",lambda:run_module("engines.affiliate_manual_manager",*args),self.refresh_affiliates)

    def add_dialog(self) -> None:
        dialog=Toplevel(self.root);dialog.title("新規アフィリエイト案件");dialog.geometry("760x760");dialog.transient(self.root);dialog.grab_set(); keys=("service","program_name","network","program_url","program_id","notes"); fields={k:StringVar() for k in keys};fields["status"]=StringVar(value="申請予定"); labels=(("サービス名（記事で使う名称・必須）","service"),("ASP案件名（正式名称・任意）","program_name"),("ASP・運営元","network"),("申請ページURL","program_url"),("プログラムID（A8.net）","program_id"),("現在の状態","status"),("メモ","notes"));form=ttk.Frame(dialog,padding=16);form.pack(fill=BOTH,expand=True)
        for row,(label,key) in enumerate(labels): ttk.Label(form,text=label).grid(row=row,column=0,sticky=W,pady=6); widget=ttk.Combobox(form,textvariable=fields[key],values=tuple(STATUS_LABELS.values()),state="readonly") if key=="status" else ttk.Entry(form,textvariable=fields[key]); widget.grid(row=row,column=1,sticky="ew",padx=(10,0),pady=6)
        ad_row=len(labels); ttk.Label(form,text="広告ソース（承認済みの場合）").grid(row=ad_row,column=0,sticky="nw",pady=6); ad_source_widget=Text(form,wrap="word",height=7,font=("Consolas",8)); ad_source_widget.grid(row=ad_row,column=1,sticky="nsew",padx=(10,0),pady=6)
        pr_row=ad_row+1; ttk.Label(form,text="PR内容・掲載条件").grid(row=pr_row,column=0,sticky="nw",pady=6); promotion_widget=Text(form,wrap="word",height=6,font=("Yu Gothic UI",9)); promotion_widget.grid(row=pr_row,column=1,sticky="nsew",padx=(10,0),pady=6)
        form.columnconfigure(1,weight=1)
        def save() -> None:
            service=fields["service"].get().strip();status=STATUS_VALUES[fields["status"].get()]
            if not service:messagebox.showwarning("入力不足","サービス名を入力してください。",parent=dialog);return
            if status=="approved" and not ad_source_widget.get("1.0",END).strip():messagebox.showwarning("入力不足","承認済みには広告ソースが必要です。",parent=dialog);return
            if fields["network"].get().strip().lower()=="a8.net" and status=="approved" and not fields["program_id"].get().strip():messagebox.showwarning("入力不足","A8.netの承認済み案件にはプログラムIDが必要です。",parent=dialog);return
            args=["add","--service",service,"--program-name",fields["program_name"].get().strip(),"--network",fields["network"].get().strip(),"--program-url",fields["program_url"].get().strip(),"--program-id",fields["program_id"].get().strip(),"--promotion-details",promotion_widget.get("1.0",END).strip(),"--status",status,"--ad-source",ad_source_widget.get("1.0",END).strip(),"--notes",fields["notes"].get().strip()];dialog.destroy();self.background("新規案件を保存中...",lambda:run_module("engines.affiliate_manual_manager",*args),self.refresh_affiliates)
        ttk.Button(form,text="案件を追加",style="Accent.TButton",command=save).grid(row=pr_row+1,column=1,sticky="e",pady=(14,0))

    def delete_affiliate(self) -> None:
        item=self.selected_affiliate()
        if not item:messagebox.showinfo("案件削除","削除する案件を選択してください。");return
        service=str(item.get("service",""))
        if messagebox.askyesno("案件を削除",f"「{service}」を管理対象から削除しますか？\n\nバックアップはPC内に残ります。"):self.background("案件を削除中...",lambda:run_module("engines.affiliate_manual_manager","delete","--service",service),self.refresh_affiliates)

    def import_affiliate_csv(self) -> None:
        selected=filedialog.askopenfilename(title="アフィリエイト案件CSVを選択",filetypes=(("CSVファイル","*.csv"),("すべてのファイル","*.*")))
        if not selected:return
        if not messagebox.askyesno("CSVをインポート",f"このCSVを読み込みますか？\n\n{selected}\n\n同じサービス名の案件は更新されます。"):return
        def task()->str:
            source=Path(selected)
            if not source.is_file():raise RuntimeError("選択したCSVを開けません。Google Drive上のファイルは、オフラインで使用可能にしてから再度お試しください。")
            with tempfile.TemporaryDirectory(prefix="alsivo-affiliate-import-") as folder:
                local_csv=Path(folder)/source.name
                try:shutil.copy2(source,local_csv)
                except OSError as error:raise RuntimeError("CSVをPC内へ読み込めません。Google Driveで『オフラインで使用可能』にするか、デスクトップへコピーしてから再度お試しください。") from error
                output=run_module("engines.affiliate_manual_manager","import-csv","--file",str(local_csv))
            data=load_json(AFFILIATE_QUEUE,{"programs":[]});count=len([item for item in data.get("programs",[]) if isinstance(item,dict)])
            return output+f"\n\n現在の登録案件: {count}件"
        self.background("CSVを読み込み中...",task,self.refresh_affiliates)

    def create_affiliate_template(self) -> None:
        candidates=[Path(os.environ.get("OneDrive",""))/"デスクトップ",Path.home()/"OneDrive"/"デスクトップ",Path.home()/"Desktop",Path.home()/"デスクトップ"]
        desktop=next((path for path in candidates if str(path) and path.is_dir()),None)
        if desktop is None:messagebox.showerror("保存先エラー","デスクトップフォルダが見つかりませんでした。");return
        output=desktop/"ALSIVO_アフィリエイト案件登録フォーマット.csv"
        if output.exists() and not messagebox.askyesno("上書き確認",f"同名のCSVがすでにあります。上書きしますか？\n\n{output}"):return
        def task()->str:
            return run_module("engines.affiliate_manual_manager","template","--output",str(output))
        self.background("CSVフォーマットを作成中...",task,self.refresh_affiliates)

    def export_a8_csv(self) -> None:
        def task() -> str:
            output=run_module("engines.a8_submission_export")
            A8_EXPORTS.mkdir(parents=True,exist_ok=True)
            webbrowser.open(A8_EXPORTS.as_uri())
            return output+"\n\n保存先フォルダを開きました。A8.netへのアップロードは手動で行ってください。"
        self.background("A8.net提出用CSVを作成中...",task,self.refresh_affiliates)

    def refresh_automation(self) -> None:
        data=load_json(LATEST_RUN,{});labels={"wait":"今回は待機（記事公開なし）","new_article":"新記事を公開","rewrite_article":"既存記事を更新"};action=str(data.get("action","不明"));self.auto_text.config(text=f"実行日時: {data.get('finished_at','記録なし')}\n結果: {data.get('status','不明')}\n判断: {labels.get(action,action)}\n{data.get('message','')}")

    def run_atlas(self,mode:str) -> None:
        messages={"dry":"公開せず安全確認を実行します。","normal":"通常の自動運転を開始します。","new":"新記事を1本生成し公開経路へ進めます。"}
        if not messagebox.askyesno("Atlasを実行",messages[mode]+"\n\n続けますか？"):return
        args={"dry":("--dry-run",),"normal":(),"new":("--force-new-article",)}[mode]
        def task()->str:
            result=subprocess.run([worker_python(),"atlas.py",*args],cwd=BASE,capture_output=True,text=True,encoding="utf-8",errors="replace",check=False,env=utf8_environment());out="\n".join(x.strip() for x in (result.stdout,result.stderr) if x.strip())
            if result.returncode:raise RuntimeError(out or "Atlasの実行に失敗しました。")
            return out or "Atlasの実行が完了しました。"
        self.background("Atlasを実行中です...",task,self.refresh)

    def background(self,message:str,task:Callable[[],str],refresh:Callable[[],None])->None:
        self.status.set(message)
        def worker()->None:
            try:output=task()
            except Exception as error:
                error_message=str(error)
                self.root.after(0,lambda error_message=error_message:self.failed(error_message))
                return
            self.root.after(0,lambda:self.finished(output,refresh))
        threading.Thread(target=worker,daemon=True).start()
    def failed(self,error:str)->None:self.status.set("処理に失敗しました。");messagebox.showerror("処理エラー",error[-5000:])
    def finished(self,output:str,refresh:Callable[[],None])->None:refresh();self.status.set("処理が完了しました。");messagebox.showinfo("完了",output[-4000:])
    @staticmethod
    def set_text(widget:Text,value:str)->None:widget.config(state="normal");widget.delete("1.0",END);widget.insert("1.0",value);widget.config(state="disabled")
    @staticmethod
    def set_text_value(widget:Text,value:str)->None:widget.delete("1.0",END);widget.insert("1.0",value)

def main()->None:
    root=Tk();App(root);root.mainloop()
if __name__=="__main__":main()
