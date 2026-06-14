# RUN_COMPOSE.md – Hướng dẫn chạy Lab 05

Tài liệu này hướng dẫn cách clone repo sạch và chạy lại Docker Compose stack của **Lab 05 – A3 Product A – Access Gate**.

Lab 05 phát triển từ Lab 04. Ở Lab 04, nhóm đã đóng gói Access Gate API bằng Docker. Sang Lab 05, nhóm mở rộng thành Docker Compose stack gồm 3 service:

* `api`: Access Gate API, chạy port `8000`
* `db`: PostgreSQL database riêng của Access Gate
* `ai-service`: AI/Risk Scoring service mô phỏng, chạy port `9000`

---

## 1. Yêu cầu môi trường

Máy cần cài sẵn:

```bash
docker version
docker compose version
node --version
npm --version
```

Trên Windows, cần mở **Docker Desktop** trước khi chạy các lệnh Docker.

Kiểm tra Docker đã chạy:

```bash
docker ps
```

Nếu lệnh trên không báo lỗi, Docker đã sẵn sàng.

---

## 2. Clone repo

```bash
git clone <repo-url>
cd lab-5-phamtuananh05
```

Nếu đã có sẵn repo trên máy, mở terminal tại thư mục chứa các file:

```text
docker-compose.yml
Dockerfile
.env.example
RUN_COMPOSE.md
contracts/
postman/
src/
db/
checklists/
```

---

## 3. Cài dependencies cho Newman/Spectral

```bash
npm install
```

Lệnh này dùng để cài các công cụ test như Newman, Spectral và HTML reporter.

Kiểm tra Newman:

```bash
npx newman --version
```

---

## 4. Tạo file `.env`

Docker Compose sử dụng file `.env` để đọc cấu hình môi trường.

Trên Linux/macOS/Git Bash:

```bash
cp .env.example .env
```

Trên Windows PowerShell:

```powershell
Copy-Item .env.example .env -Force
```

Kiểm tra nội dung:

```bash
cat .env
```

Trên Windows PowerShell:

```powershell
Get-Content .env
```

Nội dung cần có các biến chính:

```env
APP_PORT=8000
AUTH_TOKEN=lab-token
SERVICE_NAME=access-gate

POSTGRES_USER=access_gate_user
POSTGRES_PASSWORD=access_gate_password
POSTGRES_DB=access_gate_db

DB_HOST=db
DB_PORT=5432
DB_NAME=access_gate_db
DB_USER=access_gate_user
DB_PASSWORD=access_gate_password

AI_SERVICE_BASE_URL=http://ai-service:9000
```

Lưu ý: file `.env` là cấu hình local, không commit lên GitHub.

---

## 5. Kiểm tra cú pháp Docker Compose

```bash
docker compose config --quiet
```

Nếu lệnh này không in lỗi, file `docker-compose.yml` hợp lệ.

Có thể xem cấu hình Compose đã render bằng lệnh:

```bash
docker compose config
```

---

## 6. Build và chạy Docker Compose stack

Trước khi chạy lại từ đầu, dọn stack cũ nếu có:

```bash
docker compose down -v
```

Build image và khởi động các container:

```bash
docker compose up -d --build --wait
```

Lệnh trên sẽ tạo và chạy 3 service:

```text
api
db
ai-service
```

Container tương ứng:

```text
fit4110-access-gate-api-lab05
fit4110-access-gate-db-lab05
fit4110-access-gate-ai-lab05
```

Kiểm tra trạng thái container:

```bash
docker compose ps
```

Kết quả mong đợi: cả 3 service đều ở trạng thái `running` hoặc `healthy`.

---

## 7. Theo dõi log container

Xem log toàn bộ stack:

```bash
docker compose logs
```

Xem log từng service:

```bash
docker compose logs api
docker compose logs db
docker compose logs ai-service
```

Theo dõi log realtime:

```bash
docker compose logs -f
```

---

## 8. Kiểm tra API `/health`

```bash
curl -i http://localhost:8000/health
```

Trên Windows PowerShell:

```powershell
curl.exe -i http://localhost:8000/health
```

Kết quả mong đợi:

```text
HTTP/1.1 200 OK
```

Body cần có:

```json
{
  "status": "ok",
  "service": "access-gate",
  "database": {
    "required": true,
    "status": "ok"
  }
}
```

Endpoint này chứng minh Access Gate API đã chạy và kết nối được tới PostgreSQL.

---

## 9. Kiểm tra AI service `/health`

```bash
curl -i http://localhost:9000/health
```

Trên Windows PowerShell:

```powershell
curl.exe -i http://localhost:9000/health
```

Kết quả mong đợi:

```text
HTTP/1.1 200 OK
```

Body có dạng:

```json
{
  "status": "ok",
  "service": "access-gate-ai-service",
  "version": "0.5.0"
}
```

---

## 10. Kiểm tra AI `/predict`

Test thẻ hợp lệ:

```bash
curl -i -X POST http://localhost:9000/predict \
  -H "Content-Type: application/json" \
  -d '{"cardId":"card-001","gateId":"gate-main","direction":"IN"}'
```

Trên Windows PowerShell:

```powershell
curl.exe -i -X POST "http://localhost:9000/predict" -H "Content-Type: application/json" -d "{\"cardId\":\"card-001\",\"gateId\":\"gate-main\",\"direction\":\"IN\"}"
```

Kết quả mong đợi có:

```json
"riskLevel": "LOW"
```

Test thẻ bị khóa:

```bash
curl -i -X POST http://localhost:9000/predict \
  -H "Content-Type: application/json" \
  -d '{"cardId":"card-009","gateId":"gate-main","direction":"OUT"}'
```

Trên Windows PowerShell:

```powershell
curl.exe -i -X POST "http://localhost:9000/predict" -H "Content-Type: application/json" -d "{\"cardId\":\"card-009\",\"gateId\":\"gate-main\",\"direction\":\"OUT\"}"
```

Kết quả mong đợi có:

```json
"riskLevel": "HIGH"
"recommendation": "DENY"
```

---

## 11. Kiểm tra DB readiness

```bash
docker compose exec db pg_isready -U access_gate_user -d access_gate_db
```

Kết quả mong đợi:

```text
accepting connections
```

Lệnh này chứng minh PostgreSQL container đã sẵn sàng nhận kết nối.

---

## 12. Kiểm tra endpoint nghiệp vụ Access Gate

Lấy danh sách access logs:

```bash
curl -i "http://localhost:8000/access/logs/recent?limit=10" \
  -H "Authorization: Bearer lab-token"
```

Trên Windows PowerShell:

```powershell
curl.exe -i "http://localhost:8000/access/logs/recent?limit=10" -H "Authorization: Bearer lab-token"
```

Lấy thông tin thẻ:

```bash
curl -i "http://localhost:8000/cards/card-001" \
  -H "Authorization: Bearer lab-token"
```

Trên Windows PowerShell:

```powershell
curl.exe -i "http://localhost:8000/cards/card-001" -H "Authorization: Bearer lab-token"
```

Lấy trạng thái cổng:

```bash
curl -i "http://localhost:8000/gates/gate-main/status" \
  -H "Authorization: Bearer lab-token"
```

Trên Windows PowerShell:

```powershell
curl.exe -i "http://localhost:8000/gates/gate-main/status" -H "Authorization: Bearer lab-token"
```

---

## 13. Kiểm tra lỗi Auth và Validation

Thiếu token:

```bash
curl -i "http://localhost:8000/cards/card-001"
```

Kết quả mong đợi:

```text
401 Unauthorized
```

Sai giới hạn `limit`:

```bash
curl -i "http://localhost:8000/access/logs/recent?limit=999" \
  -H "Authorization: Bearer lab-token"
```

Trên Windows PowerShell:

```powershell
curl.exe -i "http://localhost:8000/access/logs/recent?limit=999" -H "Authorization: Bearer lab-token"
```

Kết quả mong đợi:

```text
422 Unprocessable Entity
```

---

## 14. Chạy Newman test trên stack Compose

```bash
npm run test:compose
```

Kết quả mong đợi ở cuối log:

```text
failed 0
```

Report được sinh tại:

```text
reports/newman-lab05-compose.xml
reports/newman-lab05-compose.html
```

Kiểm tra report:

```bash
ls reports
```

Trên Windows PowerShell:

```powershell
dir reports
```

---

## 15. Tag image theo yêu cầu nộp

Sau khi build thành công, tạo tag version:

```bash
docker tag fit4110/access-gate:lab05 fit4110/access-gate:v0.1.0-team-gate
```

Kiểm tra image:

```bash
docker images | grep access-gate
```

Trên Windows PowerShell:

```powershell
docker images | findstr access-gate
```

Cần thấy:

```text
fit4110/access-gate   lab05
fit4110/access-gate   v0.1.0-team-gate
```

Nếu cần push lên Docker Hub hoặc registry, đăng nhập và push:

```bash
docker login
docker push fit4110/access-gate:v0.1.0-team-gate
```

---

## 16. Dừng stack

Dừng container nhưng giữ volume database:

```bash
docker compose down
```

Dừng container và xóa volume database:

```bash
docker compose down -v
```

---

## 17. Lệnh chạy nhanh trên Windows PowerShell

```powershell
Copy-Item .env.example .env -Force

docker compose down -v
docker compose up -d --build --wait

docker compose ps

curl.exe -i http://localhost:8000/health
curl.exe -i http://localhost:9000/health
docker compose exec db pg_isready -U access_gate_user -d access_gate_db

curl.exe -i "http://localhost:8000/access/logs/recent?limit=10" -H "Authorization: Bearer lab-token"
curl.exe -i "http://localhost:8000/cards/card-001" -H "Authorization: Bearer lab-token"
curl.exe -i -X POST "http://localhost:9000/predict" -H "Content-Type: application/json" -d "{\"cardId\":\"card-001\",\"gateId\":\"gate-main\",\"direction\":\"IN\"}"

npm run test:compose

docker tag fit4110/access-gate:lab05 fit4110/access-gate:v0.1.0-team-gate
docker images | findstr access-gate
```

---

## 18. Mẹo gỡ lỗi

Kiểm tra trạng thái container:

```bash
docker compose ps
```

Xem log API:

```bash
docker compose logs api
```

Xem log database:

```bash
docker compose logs db
```

Xem log AI service:

```bash
docker compose logs ai-service
```

Nếu API không kết nối được DB, kiểm tra lại các biến trong `.env`:

```env
DB_HOST=db
DB_NAME=access_gate_db
DB_USER=access_gate_user
DB_PASSWORD=access_gate_password
```

Nếu Newman fail, kiểm tra lại:

```text
postman/collections/team-gate.postman_collection.json
postman/environments/team-gate_local.postman_environment.json
```

Đảm bảo environment đang dùng:

```text
baseUrl = http://localhost:8000
aiServiceUrl = http://localhost:9000
authToken = lab-token
```

---

## 19. Artefact cần nộp

Các file/evidence chính cần có:

```text
docker-compose.yml
.dockerignore
.env.example
RUN_COMPOSE.md
contracts/team-gate.openapi.yaml
postman/environments/team-gate_local.postman_environment.json
reports/newman-lab05-compose.xml
reports/newman-lab05-compose.html
reports/screenshots/
checklists/readiness-checklist.md
```

Image tag cần có:

```text
fit4110/access-gate:v0.1.0-team-gate
```
