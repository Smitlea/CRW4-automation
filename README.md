# CRW4AutoMation CRW4自動化行程工具 

## CRW4Automation
An project & customizable UI for CRW4 aim to assisst labotory for automatic and scheduable chemicals search with CRW4(Chemical Reactivity Worksheet 4), an close and outdated application publish by AIChE, yet been use worldwide due to it's strict and precise harm prediction。

![upload_6d6ba7fce9c2087d48fa1f70a603cf5d](https://github.com/user-attachments/assets/421fd7bf-9cbe-4ca5-9cae-189fd55db90c)

## Installation

- First clone the project
```CMD= 
git clone https://github.com/Smitlea/CRW4-automation.git 
```

- then install requirements
```CMD=
pip install -r requirements
```
- change redis commander password and user name
```CMD=
nano docker-compose.yml
```

- with Dokcer(recommanded)
- Set up Redis and it's command-panel(Optional)
```CMD=
docker compose up -d
```
:::warning
Warning:
Redis commander Default User and Password should config
through docker-compose.yml or not to be use at all
:::

- Set up Celery 
```CMD=
celery -A tasks.Celery_app worker -l INFO --pool=solo
```

- Set up Swagger
```CMD=
 python app.py
```


## CRW4 Flask Backend Endpoint app.py 

| Method | URL Path | Description | Note |
| - | - | - | - |
| POST | /queue| 發送任務請求 |  |
| GET | /result | 取得task狀態 |  |

## CRW4 Backend Endpoint test.py

Redis_commander:\<Domain>\:8081
Swagger: \<Domain\>/api/doc  

| Method | URL Path | Description | Note |
| - | - | - | - |
| GET | /start | 開始程式 | 
| GET | /clear_mixture | 清除所有化合物 | |
| GET | /show | 測試用API | 該功能為開發者使用 |
| GET | /render | 輸出CSV檔案 |  |
| POST | /mulitiple_search | 主要功能提供多次搜尋|  |
| POST | /generate_json | 多次搜尋並顯示化合物搜尋狀態 |  |
| POST | /mulitiple_select_and_render | 多次搜尋並輸出CSV檔案|  |

## Structure

![CRW4流程圖v2 drawio](https://github.com/user-attachments/assets/a8f086e8-1e53-42d4-ac92-2bc2ef91aaef)
