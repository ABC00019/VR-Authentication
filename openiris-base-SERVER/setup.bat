python -m venv .venv
call .venv\Scripts\activate
pip install -r open-iris\requirements\base.txt
pip install -e .\open-iris
echo Setup complete.
pause