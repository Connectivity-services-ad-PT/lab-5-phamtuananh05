# Readiness Checklist – Lab 05 – Access Gate

Nhóm: A3 – Product A – Access Gate  
Team: team-gate  
Service chính: Access Gate API  
Stack: API + PostgreSQL Database + AI/Risk Scoring service

- [x] **Database ready:** service `db` chạy PostgreSQL và phản hồi `pg_isready` với user `access_gate_user`.
- [x] **AI service ready:** service `ai-service` trả `200 OK` cho endpoint `/health` trên port `9000`.
- [x] **AI predict ready:** service `ai-service` có endpoint `/predict` để mô phỏng đánh giá rủi ro truy cập tại cổng.
- [x] **API ready:** service `api` trả `200 OK` cho endpoint `/health` trên port `8000`.
- [x] **Environment variables:** `.env.example` khai báo đầy đủ `APP_PORT`, `AUTH_TOKEN`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- [x] **Network & ports:** API expose port `8000`, AI service expose port `9000`, DB nằm trong network nội bộ `team-internal`.
- [x] **Image tags:** API image sử dụng tag `fit4110/access-gate:lab05`, có thể tag thêm `fit4110/access-gate:v0.1.0-team-gate` khi nộp.
- [x] **Auth:** các endpoint nghiệp vụ của Access Gate yêu cầu `Authorization: Bearer lab-token`.
- [x] **Error handling:** lỗi auth, validation và not found trả về dạng ProblemDetails.
- [x] **Compose readiness:** lệnh `docker compose up -d --build --wait` chạy được toàn bộ stack `api`, `db`, `ai-service`.

Ghi chú:

```text
Lab 05 phát triển từ Lab 04 của nhóm A3 Access Gate. Stack được mở rộng từ một API container sang Docker Compose gồm API, PostgreSQL database và AI/Risk Scoring service mô phỏng.