# README_REPO

## 1. Giới thiệu bài toán

Đây là project demo hệ thống gợi ý sản phẩm bằng Neo4j.

Ý tưởng chính:
- lưu dữ liệu người dùng, sản phẩm, danh mục và hành vi mua hàng dưới dạng graph
- dùng Cypher query để suy ra recommendation
- lấy dữ liệu thật từ BigQuery public dataset `thelook_ecommerce`

Graph model hiện tại:

```text
(User)-[:PURCHASED]->(Product)-[:BELONGS_TO]->(Category)
```

## 2. Mục tiêu bài demo

Project này nhằm chứng minh:
1. Neo4j phù hợp với bài toán có nhiều mối quan hệ.
2. Recommendation có thể làm được bằng graph model và Cypher.
3. Dữ liệu từ BigQuery có thể import vào Neo4j để tạo recommendation demo.
4. Có thể gợi ý theo user-based và category-based.

## 3. Nguồn dữ liệu hiện tại

Project hiện tại đã chuyển sang dùng BigQuery public dataset:

- `bigquery-public-data.thelook_ecommerce`

Bảng dữ liệu được dùng:
- `users`
- `orders`
- `order_items`
- `products`

Project Google Cloud để chạy query của bạn:
- `neo4j-bigquery-demo`

Lưu ý:
- data nằm ở `bigquery-public-data`
- project `neo4j-bigquery-demo` được dùng để gửi query job và quota

## 4. Luồng xử lý tổng thể

### Bước 1. Xác thực Google Cloud

Máy cần đăng nhập `gcloud auth application-default login`.

`.env` cần có:

```env
GOOGLE_CLOUD_PROJECT=neo4j-bigquery-demo
```

### Bước 2. Đọc dữ liệu từ BigQuery

File:
- `src/bigquery_data/fetch_from_bigquery.py`

Project đọc dữ liệu bằng query join:
- `orders`
- `order_items`
- `users`
- `products`

Kết quả mỗi dòng gồm:
- `user_id`
- `first_name`
- `last_name`
- `product_id`
- `product_name`
- `category_name`

### Bước 3. Import vào Neo4j

File:
- `src/bigquery_data/set_up_database_using_bigquery.py`

Project sẽ:
- tạo constraint
- clear dữ liệu cũ nếu cần
- `MERGE` user
- `MERGE` product
- `MERGE` category
- `MERGE` relationship `PURCHASED`
- `MERGE` relationship `BELONGS_TO`

### Bước 4. Chạy recommendation

File:
- `src/recommendations/collaborative_filtering.py`

Có 2 kiểu recommendation:
- `user-based`
- `category-based`

## 5. Giải thích recommendation hiện tại

### 5.1. User-based recommendation

Logic hiện tại đã được cải thiện để bớt bị rỗng:
- tìm các user mua trùng sản phẩm với target user
- chấm điểm theo mức độ overlap
- boost thêm các sản phẩm thuộc category mà target user đã thích
- nếu graph còn thưa, fallback bằng category + popularity để vẫn trả về kết quả hợp lý

Ý nghĩa:
- không chỉ nhìn người dùng giống nhau
- mà còn tận dụng sở thích category của user
- giúp kết quả ổn hơn khi sample dữ liệu chưa lớn

### 5.2. Category-based recommendation

Logic:
- tìm category user mua nhiều nhất
- lấy các product khác trong category đó
- loại các product đã mua
- trả về danh sách còn lại

## 6. Các file quan trọng

- `src/main.py`
- `src/database/database_setup.py`
- `src/bigquery_data/fetch_from_bigquery.py`
- `src/bigquery_data/set_up_database_using_bigquery.py`
- `src/recommendations/collaborative_filtering.py`
- `.env`

## 7. Cách chạy project

### 7.1. Cài thư viện

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 7.2. Import data từ BigQuery và chạy recommendation

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m src.main --bootstrap-bigquery --project-id neo4j-bigquery-demo --limit 2000 --user-id 1
```

Flag hữu ích:
- `--limit 500`
- `--limit 2000`
- `--keep-existing-data`

Nếu chỉ muốn chạy recommendation trên data đã import sẵn:

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m src.main --user-id 1
```

## 8. Cách kiểm tra dữ liệu trên Neo4j

Tổng node:

```cypher
MATCH (n) RETURN count(n) AS total_nodes
```

Tổng relationship:

```cypher
MATCH ()-[r]->() RETURN count(r) AS total_relationships
```

Xem graph:

```cypher
MATCH (u:User)-[r1:PURCHASED]->(p:Product)-[r2:BELONGS_TO]->(c:Category)
RETURN u, r1, p, r2, c
LIMIT 50
```

Xem user 1 đã mua gì:

```cypher
MATCH (u:User {id: '1'})-[:PURCHASED]->(p:Product)
RETURN u, p
```

Xem user 1 thường mua category nào:

```cypher
MATCH (u:User {id: '1'})-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(c:Category)
RETURN c.name AS category, count(*) AS so_lan_mua
ORDER BY so_lan_mua DESC
```

Xem top 10 product được mua nhiều nhất:

```cypher
MATCH (:User)-[:PURCHASED]->(p:Product)
RETURN p.title AS product, count(*) AS so_lan_duoc_mua
ORDER BY so_lan_duoc_mua DESC
LIMIT 10
```

Xem top 10 category được mua nhiều nhất:

```cypher
MATCH (:User)-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(c:Category)
RETURN c.name AS category, count(*) AS tong_luot_mua
ORDER BY tong_luot_mua DESC
LIMIT 10
```

Xem các user giống user 1 theo sản phẩm mua chung:

```cypher
MATCH (target:User {id: '1'})-[:PURCHASED]->(p:Product)
MATCH (similar:User)-[:PURCHASED]->(p)
WHERE similar <> target
RETURN similar.id AS similar_user, count(DISTINCT p) AS shared_products
ORDER BY shared_products DESC
LIMIT 10
```

Xem recommendation user-based trực tiếp:

```cypher
MATCH (target:User {id: '1'})-[:PURCHASED]->(p:Product)
MATCH (similar:User)-[:PURCHASED]->(p)
WHERE similar <> target
WITH target, similar, count(DISTINCT p) AS shared_products
ORDER BY shared_products DESC
LIMIT 25
MATCH (similar)-[:PURCHASED]->(recommended:Product)-[:BELONGS_TO]->(recommended_category:Category)
WHERE NOT (target)-[:PURCHASED]->(recommended)
OPTIONAL MATCH (target)-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(target_category:Category)
WITH recommended.title AS product,
     shared_products,
     recommended_category.name AS recommended_category,
     collect(DISTINCT target_category.name) AS target_categories
RETURN product,
       sum(shared_products) AS shared_signal,
       sum(CASE WHEN recommended_category IN target_categories THEN 1 ELSE 0 END) AS category_signal
ORDER BY shared_signal DESC, category_signal DESC, product ASC
LIMIT 5
```

Xem recommendation category-based trực tiếp:

```cypher
MATCH (u:User {id: '1'})-[:PURCHASED]->(p:Product)-[:BELONGS_TO]->(c:Category)
WITH u, c.name AS category, count(*) AS cnt
ORDER BY cnt DESC
LIMIT 1
MATCH (:Category {name: category})<-[:BELONGS_TO]-(q:Product)
WHERE NOT (u)-[:PURCHASED]->(q)
RETURN category, q.title AS recommendation
ORDER BY recommendation
LIMIT 5
```

Xem product nào thuộc một category cụ thể:

```cypher
MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: 'Shorts'})
RETURN p.title AS product
ORDER BY product
LIMIT 20
```

Xem user nào đã mua một product cụ thể:

```cypher
MATCH (u:User)-[:PURCHASED]->(p:Product {title: "Lucky Brand Men's Printed Baja Short"})
RETURN u.id AS user_id, u.name AS user_name
LIMIT 20
```

## 9. Kết quả demo hiện tại

Với `user_id = 1`, project hiện tại đã cho ra:
- user-based recommendation có kết quả
- category-based recommendation có kết quả

Điều này cho thấy:
- BigQuery đã đọc dữ liệu thành công
- Neo4j đã nhận graph data thành công
- recommendation đã hoạt động trên dữ liệu thật

## 10. Điểm mạnh

- dùng dữ liệu thật từ BigQuery public dataset
- graph model dễ giải thích
- recommendation dễ demo với leader
- có thể mở rộng thêm score, review, viewed, added-to-cart

## 11. Hạn chế hiện tại

- vẫn là demo, chưa phải production system
- chưa có giao diện web
- chưa có weighted time-decay
- chưa có hybrid ML/embedding
- recommendation user-based vẫn phụ thuộc vào mức độ dày của graph

## 12. Câu kết luận để thuyết trình

Có thể nói gọn:

> Project này dùng BigQuery public dataset để lấy dữ liệu mua hàng, đưa vào Neo4j thành graph quan hệ, rồi dùng Cypher để sinh gợi ý sản phẩm theo user similarity và category preference một cách trực quan, dễ giải thích và dễ demo.
