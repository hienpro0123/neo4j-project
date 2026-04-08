# README_REPO

## 1. Gioi thieu bai toan

Day la project demo he thong goi y san pham bang Neo4j.

Y tuong chinh:
- luu du lieu nguoi dung, san pham, danh muc va hanh vi mua hang duoi dang graph
- dung Cypher query de suy ra recommendation
- lay du lieu that tu BigQuery public dataset `thelook_ecommerce`

Graph model hien tai:

```text
(User)-[:PURCHASED]->(Product)-[:BELONGS_TO]->(Category)
```

## 2. Muc tieu bai demo

Project nay nham chung minh:
1. Neo4j phu hop voi bai toan co nhieu moi quan he.
2. Recommendation co the lam duoc bang graph model va Cypher.
3. Du lieu tu BigQuery co the import vao Neo4j de tao recommendation demo.
4. Co the goi y theo user-based va category-based.

## 3. Nguon du lieu hien tai

Project hien tai da chuyen sang dung BigQuery public dataset:

- `bigquery-public-data.thelook_ecommerce`

Bang du lieu duoc dung:
- `users`
- `orders`
- `order_items`
- `products`

Project Google Cloud de chay query cua ban:
- `neo4j-bigquery-demo`

Luu y:
- data nam o `bigquery-public-data`
- project `neo4j-bigquery-demo` duoc dung de gui query job va quota

## 4. Luong xu ly tong the

### Buoc 1. Xac thuc Google Cloud

May can dang nhap `gcloud auth application-default login`.

`.env` can co:

```env
GOOGLE_CLOUD_PROJECT=neo4j-bigquery-demo
```

### Buoc 2. Doc du lieu tu BigQuery

File:
- `src/bigquery_data/fetch_from_bigquery.py`

Project doc du lieu bang query join:
- `orders`
- `order_items`
- `users`
- `products`

Ket qua moi dong gom:
- `user_id`
- `first_name`
- `last_name`
- `product_id`
- `product_name`
- `category_name`

### Buoc 3. Import vao Neo4j

File:
- `src/bigquery_data/set_up_database_using_bigquery.py`

Project se:
- tao constraint
- clear du lieu cu neu can
- `MERGE` user
- `MERGE` product
- `MERGE` category
- `MERGE` relationship `PURCHASED`
- `MERGE` relationship `BELONGS_TO`

### Buoc 4. Chay recommendation

File:
- `src/recommendations/collaborative_filtering.py`

Co 2 kieu recommendation:
- `user-based`
- `category-based`

## 5. Giai thich recommendation hien tai

### 5.1. User-based recommendation

Logic hien tai da duoc cai thien de bot bi rong:
- tim cac user mua trung san pham voi target user
- cham diem theo muc do overlap
- boost them cac san pham thuoc category ma target user da thich
- neu graph con thua, fallback bang category + popularity de van tra ve ket qua hop ly

Y nghia:
- khong chi nhin nguoi dung giong nhau
- ma con tan dung so thich category cua user
- giup ket qua on hon khi sample du lieu chua lon

### 5.2. Category-based recommendation

Logic:
- tim category user mua nhieu nhat
- lay cac product khac trong category do
- loai cac product da mua
- tra ve danh sach con lai

## 6. Cac file quan trong

- `src/main.py`
- `src/database/database_setup.py`
- `src/bigquery_data/fetch_from_bigquery.py`
- `src/bigquery_data/set_up_database_using_bigquery.py`
- `src/recommendations/collaborative_filtering.py`
- `.env`

## 7. Cach chay project

### 7.1. Cai thu vien

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 7.2. Import data tu BigQuery va chay recommendation

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m src.main --bootstrap-bigquery --project-id neo4j-bigquery-demo --limit 2000 --user-id 1
```

Flag huu ich:
- `--limit 500`
- `--limit 2000`
- `--keep-existing-data`

Neu chi muon chay recommendation tren data da import san:

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m src.main --user-id 1
```

## 8. Cach kiem tra du lieu tren Neo4j

Tong node:

```cypher
MATCH (n) RETURN count(n) AS total_nodes
```

Tong relationship:

```cypher
MATCH ()-[r]->() RETURN count(r) AS total_relationships
```

Xem graph:

```cypher
MATCH (u:User)-[r1:PURCHASED]->(p:Product)-[r2:BELONGS_TO]->(c:Category)
RETURN u, r1, p, r2, c
LIMIT 50
```

Xem user 1 da mua gi:

```cypher
MATCH (u:User {id: '1'})-[:PURCHASED]->(p:Product)
RETURN u, p
```

Xem user 1 thuong mua category nao:

```cypher
MATCH (u:User {id: '1'})-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(c:Category)
RETURN c.name AS category, count(*) AS so_lan_mua
ORDER BY so_lan_mua DESC
```

Xem top 10 product duoc mua nhieu nhat:

```cypher
MATCH (:User)-[:PURCHASED]->(p:Product)
RETURN p.title AS product, count(*) AS so_lan_duoc_mua
ORDER BY so_lan_duoc_mua DESC
LIMIT 10
```

Xem top 10 category duoc mua nhieu nhat:

```cypher
MATCH (:User)-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(c:Category)
RETURN c.name AS category, count(*) AS tong_luot_mua
ORDER BY tong_luot_mua DESC
LIMIT 10
```

Xem cac user giong user 1 theo san pham mua chung:

```cypher
MATCH (target:User {id: '1'})-[:PURCHASED]->(p:Product)
MATCH (similar:User)-[:PURCHASED]->(p)
WHERE similar <> target
RETURN similar.id AS similar_user, count(DISTINCT p) AS shared_products
ORDER BY shared_products DESC
LIMIT 10
```

Xem recommendation user-based truc tiep:

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

Xem recommendation category-based truc tiep:

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

Xem product nao thuoc mot category cu the:

```cypher
MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: 'Shorts'})
RETURN p.title AS product
ORDER BY product
LIMIT 20
```

Xem user nao da mua mot product cu the:

```cypher
MATCH (u:User)-[:PURCHASED]->(p:Product {title: "Lucky Brand Men's Printed Baja Short"})
RETURN u.id AS user_id, u.name AS user_name
LIMIT 20
```

## 9. Ket qua demo hien tai

Voi `user_id = 1`, project hien tai da cho ra:
- user-based recommendation co ket qua
- category-based recommendation co ket qua

Dieu nay cho thay:
- BigQuery da doc du lieu thanh cong
- Neo4j da nhan graph data thanh cong
- recommendation da hoat dong tren du lieu that

## 10. Diem manh

- dung du lieu that tu BigQuery public dataset
- graph model de giai thich
- recommendation de demo voi leader
- co the mo rong them score, review, viewed, added-to-cart

## 11. Han che hien tai

- van la demo, chua phai production system
- chua co giao dien web
- chua co weighted time-decay
- chua co hybrid ML/embedding
- recommendation user-based van phu thuoc vao muc do day cua graph

## 12. Cau ket luan de thuyet trinh

Co the noi gon:

> Project nay dung BigQuery public dataset de lay du lieu mua hang, dua vao Neo4j thanh graph quan he, roi dung Cypher de sinh goi y san pham theo user similarity va category preference mot cach truc quan, de giai thich va de demo.
