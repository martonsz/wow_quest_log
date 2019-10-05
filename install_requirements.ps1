# Creates a virtuelenv and installs dependencies in requirements.txt
$path = '.venv'
if (-Not (Test-Path $path)) {
	""
	"Creating virtualenv at $path"
	""
	python -m venv .venv
}

& .\${path}\Scripts\Activate.ps1
pip install -r requirements.txt
