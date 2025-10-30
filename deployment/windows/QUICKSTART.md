# Windows本番環境 クイックスタートガイド

## 5分でできる！セットアップ手順

### 前提条件

✅ Windows Server 2019以上 または Windows 10/11 Pro  
✅ Python 3.11以上がインストール済み  
✅ 管理者権限でPowerShellを実行可能  

---

## ステップ1: プロジェクト配置

プロジェクトを `C:\BackupSystem` に配置してください。

---

## ステップ2: PowerShell起動

**PowerShellを右クリック → 「管理者として実行」**

```powershell
cd C:\BackupSystem\deployment\windows
```

---

## ステップ3: 実行ポリシー設定（初回のみ）

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## ステップ4: 環境セットアップ（5分）

```powershell
.\setup.ps1
```

**入力事項**:
- 管理者ユーザー名（例: admin）
- 管理者メールアドレス（例: admin@example.com）
- 管理者パスワード（強力なパスワード）

---

## ステップ5: サービスインストール（2分）

```powershell
.\install_service.ps1
```

NSSMが自動ダウンロードされ、サービスが起動します。

---

## ステップ6: ファイアウォール設定（1分）

```powershell
.\configure_firewall.ps1
```

ポート5000が開放されます。

---

## ステップ7: 確認

```powershell
.\verify_installation.ps1
```

すべて✓（成功）であることを確認してください。

---

## ステップ8: アクセス

Webブラウザで以下にアクセス:

```
http://localhost:5000
http://192.168.3.135:5000
```

**ログイン**:
- ユーザー名: admin（または設定した値）
- パスワード: セットアップ時に設定

---

## 完了！🎉

システムが正常に起動しました。

### 便利なコマンド

```powershell
# サービス再起動
Restart-Service BackupManagementSystem

# ログ確認
Get-Content C:\BackupSystem\logs\app.log -Tail 50 -Wait

# サービス状態確認
Get-Service BackupManagementSystem
```

---

## トラブル時

詳細は `README.md` の「トラブルシューティング」セクションを参照してください。

```powershell
# エラーログ確認
Get-Content C:\BackupSystem\logs\service_stderr.log -Tail 50
```

---

## 次のステップ

1. `.env` ファイルでSECRET_KEYを変更（推奨）
2. HTTPSを有効化（本番環境では必須）
3. メール通知を設定（オプション）
4. Teams通知を設定（オプション）

詳細は `README.md` を参照してください。
