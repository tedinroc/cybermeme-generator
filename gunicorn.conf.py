import multiprocessing

# 根據 CPU 核心數設定 workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gthread'
threads = 4

# 監聽所有網絡介面
bind = '0.0.0.0:$PORT'

# 請求超時設定
timeout = 300
keepalive = 5

# 記錄設定
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# 優化設定
worker_tmp_dir = '/dev/shm'
max_requests = 1000
max_requests_jitter = 50
