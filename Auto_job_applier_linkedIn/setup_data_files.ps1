# Script de Setup - Criar arquivos de dados a partir dos templates
# Execute este script após clonar o repositório

Write-Host "🔧 Configurando arquivos de dados..." -ForegroundColor Cyan

$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$excelDir = Join-Path $baseDir "all excels"

# Criar arquivos CSV se não existirem
$files = @(
    @{
        template = Join-Path $excelDir "all_applied_applications_history.csv.template"
        target = Join-Path $excelDir "all_applied_applications_history.csv"
    },
    @{
        template = Join-Path $excelDir "all_failed_applications_history.csv.template"
        target = Join-Path $excelDir "all_failed_applications_history.csv"
    }
)

foreach ($file in $files) {
    if (-not (Test-Path $file.target)) {
        Write-Host "📄 Criando: $($file.target)" -ForegroundColor Green
        Copy-Item $file.template $file.target
    } else {
        Write-Host "✅ Já existe: $($file.target)" -ForegroundColor Yellow
    }
}

Write-Host "`n✨ Setup completo! Agora você pode executar o bot." -ForegroundColor Green
Write-Host "⚠️  Lembre-se: Os arquivos CSV não são versionados no Git." -ForegroundColor Yellow
Write-Host "💾 Faça backups regulares dos seus dados!" -ForegroundColor Cyan
