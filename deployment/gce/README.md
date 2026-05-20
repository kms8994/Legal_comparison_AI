# GCE 배포 가이드

국가법령정보 API 연동을 위해 먼저 Google Compute Engine VM과 고정 외부 IP를 만든다.

## 1. GCP에서 고정 IP 준비

1. VPC Network > IP addresses로 이동한다.
2. `Reserve external static IP address`를 선택한다.
3. Region은 VM과 같은 리전으로 둔다. 예: `asia-northeast3` 또는 프로젝트에서 쓰는 리전.
4. 생성한 static IP를 메모한다.
5. 국가법령정보 API 신청/설정 화면에 이 static IP를 등록한다.

## 2. VM 생성

권장 시작값:

- OS: Ubuntu 22.04 LTS
- Machine type: e2-micro 또는 e2-small
- Boot disk: 20GB 이상
- Firewall: HTTP 허용
- External IP: 위에서 예약한 static IP 지정

## 3. VM에 Docker 설치

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

설치 후 SSH를 다시 접속한다.

## 4. 코드 배포

```bash
git clone https://github.com/kms8994/Legal_comparison_AI.git
cd Legal_comparison_AI
git checkout work/desktop
```

`backend/.env`를 만든다.

```env
APP_ENV=production
CORS_ORIGINS=["http://YOUR_STATIC_IP"]
DATABASE_URL=postgresql+psycopg://...
LAW_OPEN_API_OC=...
```

## 5. 서버 실행

```bash
docker compose -f deployment/gce/docker-compose.yml up -d --build
```

확인:

```bash
curl http://YOUR_STATIC_IP/api/health
```

브라우저:

```text
http://YOUR_STATIC_IP
```

## 6. 판례 수집 실행

```bash
docker compose -f deployment/gce/docker-compose.yml exec backend \
  python -m pipelines.collector.collect_precedents --query 교통사고 --pages 1 --display 10
```

## 7. 운영 메모

- `backend/.env`는 서버에만 둔다.
- 국가법령정보 API에는 VM의 static IP를 등록한다.
- HTTPS가 필요해지면 nginx에 도메인과 인증서를 붙인다.
- 첫 수집은 `--display 5` 정도로 작게 시작해서 필드 매핑을 검수한다.
