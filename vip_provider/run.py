# /run-run.py
from vip_provider.app import app

# LOCAL
if __name__ == '__main__':
  """
  app run
  """
  app.run(port=int('8888'), host='0.0.0.0')
# LOCAL
