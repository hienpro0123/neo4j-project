# README_REPO

## 1. Giới thiệu bài toán

Đây là dự án demo hệ thống gợi ý sản phẩm bằng graph database Neo4j, sử dụng dữ liệu thật từ BigQuery.

Mục tiêu chính:
- Mô hình hóa hành vi mua hàng dưới dạng đồ thị quan hệ.
- Truy vấn suy luận bằng Cypher để tạo khuyến nghị.
- Chứng minh luồng dữ liệu end-to-end từ BigQuery sang Neo4j rồi sinh recommendation.

Mô hình graph lõi hiện tại:

```text
(User)-[:PURCHASED]->(Product)-[:BELONGS_TO]->(Category)
```

## 2. Mục tiêu có thể báo cáo khi thuyết trình

1. Chứng minh Neo4j phù hợp bài toán recommendation dựa trên quan hệ.
2. Chứng minh pipeline dữ liệu hoạt động ổn định: BigQuery -> Neo4j -> Recommendation output.
3. Trình bày 2 chiến lược gợi ý hiện có:
- User-based collaborative filtering (có fallback để giảm rỗng kết quả).
- Category-based recommendation.
4. Chứng minh khả năng mở rộng dễ: thêm loại quan hệ mới mà không phá mô hình cũ.

## 3. Phạm vi dữ liệu và nguồn dữ liệu

Nguồn dữ liệu:
- `bigquery-public-data.thelook_ecommerce`

Bảng được join để lấy dữ liệu:
- `orders`
- `order_items`
- `users`
- `products`

Các trường chính đang import vào graph:
- `user_id`, `first_name`, `last_name`
- `product_id`, `product_name`
- `category_name`

Lưu ý triển khai:
- Dữ liệu nằm ở project public `bigquery-public-data`.
- Project GCP của bạn (ví dụ `neo4j-bigquery-demo`) dùng để chạy query job và tính quota.

## 4. Kiến trúc và luồng xử lý tổng thể

4.1. Luồng chạy end-to-end

1. Đọc cấu hình kết nối từ `.env`.
2. (Tuỳ chọn) Bootstrap dữ liệu từ BigQuery sang Neo4j.
3. Tạo constraint trong Neo4j.
4. Chạy 2 hàm recommendation cho `user_id` được chọn.
5. In kết quả gợi ý ra terminal.

4.2. Các file đóng vai trò chính

- `src/main.py`: entrypoint CLI, parse tham số và điều phối luồng.
- `src/database/database_setup.py`: kết nối Neo4j, create constraint, clear DB.
- `src/bigquery_data/fetch_from_bigquery.py`: truy vấn BigQuery.
- `src/bigquery_data/set_up_database_using_bigquery.py`: import row-by-row vào graph.
- `src/recommendations/collaborative_filtering.py`: thuật toán gợi ý user-based và category-based.

## 5. Thiết kế dữ liệu trong Neo4j

5.1. Node labels

- `User`
- `Product`
- `Category`

5.2. Relationship types

- `(:User)-[:PURCHASED]->(:Product)`
- `(:Product)-[:BELONGS_TO]->(:Category)`

5.3. Constraints đang có trong code

- Unique `User.id`
- Unique `Product.id`
- Unique `Category.name`

Ý nghĩa:
- Tránh trùng node khi import nhiều lần.
- Tăng tốc lookup và đảm bảo nhất quán dữ liệu.

## 6. Giải thích thuật toán recommendation hiện tại

6.1. User-based collaborative filtering

Ý tưởng:
1. Tìm nhóm user mua trùng sản phẩm với user mục tiêu.
2. Chấm điểm tín hiệu dựa trên số sản phẩm mua chung (`shared_products`).
3. Lấy sản phẩm mà nhóm user tương đồng đã mua nhưng user mục tiêu chưa mua.
4. Cộng điểm ưu tiên nếu sản phẩm thuộc category user mục tiêu từng mua.
5. Xếp hạng theo công thức tổng hợp và trả về `top_n`.

Fallback khi dữ liệu thưa:
- Nếu chưa đủ `top_n`, hệ thống chuyển sang truy vấn category + popularity để bổ sung.
- Giúp giảm tình trạng danh sách recommendation rỗng.

6.2. Category-based recommendation

Ý tưởng:
1. Tìm category user mục tiêu mua nhiều nhất.
2. Lấy các product cùng category đó mà user chưa mua.
3. Sắp xếp theo tên sản phẩm và trả về `top_n`.

## 7. Cách chạy demo chuẩn để báo cáo

7.1. Cài môi trường

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

7.2. Khai báo `.env`

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
GOOGLE_CLOUD_PROJECT=neo4j-bigquery-demo
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
```

7.3. Chạy bootstrap + recommendation

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m src.main --bootstrap-bigquery --project-id neo4j-bigquery-demo --limit 2000 --user-id 1
```

7.4. Chỉ chạy recommendation (không import lại)

```powershell
$env:PYTHONPATH='.'
.\.venv\Scripts\python.exe -m src.main --user-id 1
```

7.5. Tham số CLI hữu ích

- `--bootstrap-bigquery`: bật import từ BigQuery.
- `--project-id`: chỉ định project chạy query BigQuery.
- `--limit 500|2000|...`: giới hạn số dòng import.
- `--keep-existing-data`: không xóa graph cũ trước khi import.
- `--user-id`: user cần gợi ý.

## 8. Checklist chứng minh hệ thống hoạt động

1. Kiểm tra tổng node:

```cypher
MATCH (n)
RETURN count(n) AS total_nodes;
```

Ý nghĩa: kiểm tra nhanh tổng quy mô graph sau khi import dữ liệu.
Kết quả mong đợi: trả về một số nguyên `total_nodes`, thường lớn hơn 0 nếu import thành công.

2. Kiểm tra tổng relationship:

```cypher
MATCH ()-[r]->()
RETURN count(r) AS total_relationships;
```

Ý nghĩa: kiểm tra tổng số quan hệ đang có trong graph.
Kết quả mong đợi: trả về một số nguyên `total_relationships`, giúp bạn đối chiếu với tổng node ở trên.

3. Kiểm tra schema chính:

```cypher
MATCH (u:User)-[r1:PURCHASED]->(p:Product)-[r2:BELONGS_TO]->(c:Category)
RETURN u, r1, p, r2, c
LIMIT 50;
```

Ý nghĩa: xem trực quan schema cốt lõi `User -> Product -> Category` có được tạo đúng không.
Kết quả mong đợi: Neo4j Browser hiện các node và relationship mẫu để bạn xác nhận dữ liệu nối đúng.

4. Kiểm tra lịch sử mua của user cụ thể:

```cypher
MATCH (u:User)-[:PURCHASED]->(p:Product)
WHERE toString(u.id) = '1'
RETURN u.id AS user_id, p.id AS product_id, p.title AS product_name
ORDER BY p.title
LIMIT 30;
```

Ý nghĩa: kiểm tra lịch sử mua của một user cụ thể trước khi chạy recommendation.
Kết quả mong đợi: trả về danh sách sản phẩm mà user `1` đã mua, sắp theo tên sản phẩm.

## 9. 20 câu lệnh Cypher mới về quan hệ (dùng trực tiếp trên Neo4j)

Lưu ý:
- Các lệnh bên dưới tập trung vào relationship.
- Có cả nhóm đọc/phân tích và nhóm tạo quan hệ dẫn xuất để phục vụ demo nâng cao.
- Nên chạy theo thứ tự từ 1 -> 20 để dễ giải thích.

1) Đếm số `PURCHASED` theo user

```cypher
MATCH (u:User)-[r:PURCHASED]->(:Product)
RETURN u.id AS user_id, count(r) AS purchased_count
ORDER BY purchased_count DESC
LIMIT 20;
```

Ý nghĩa: đếm xem mỗi user đã mua bao nhiêu sản phẩm.
Kết quả mong đợi: trả về danh sách user và số lượt `PURCHASED`, các user mua nhiều nhất nằm trên cùng.

2) Đếm số user đã mua theo product

```cypher
MATCH (:User)-[r:PURCHASED]->(p:Product)
RETURN p.id AS product_id, p.title AS product_name, count(r) AS buyer_count
ORDER BY buyer_count DESC
LIMIT 20;
```

Ý nghĩa: tìm các sản phẩm được nhiều user mua nhất.
Kết quả mong đợi: trả về product id, tên sản phẩm và số người mua, sắp xếp giảm dần theo `buyer_count`.

3) Đếm số product trong mỗi category qua `BELONGS_TO`

```cypher
MATCH (p:Product)-[r:BELONGS_TO]->(c:Category)
RETURN c.name AS category, count(r) AS product_count
ORDER BY product_count DESC;
```

Ý nghĩa: kiểm tra category nào đang chứa nhiều sản phẩm nhất trong graph.
Kết quả mong đợi: trả về tên category và số product thuộc category đó.

4) Tìm product chưa có quan hệ `BELONGS_TO`

```cypher
MATCH (p:Product)
WHERE NOT (p)-[:BELONGS_TO]->(:Category)
RETURN p.id AS product_id, p.title AS product_name
LIMIT 50;
```

Ý nghĩa: rà dữ liệu lỗi, tức product chưa được gắn category.
Kết quả mong đợi: nếu dữ liệu sạch thì không có bản ghi nào; nếu có lỗi sẽ hiện danh sách product bị thiếu `BELONGS_TO`.

Nếu Neo4j trả về `No changes, no records` thì đây không phải lỗi. Nó chỉ có nghĩa là hiện tại không có `Product` nào bị thiếu quan hệ `BELONGS_TO`.

5) Tìm user chưa có quan hệ `PURCHASED`

```cypher
MATCH (u:User)
WHERE NOT (u)-[:PURCHASED]->(:Product)
RETURN u.id AS user_id, u.display_name AS user_name
LIMIT 50;
```

Ý nghĩa: tìm các user tồn tại trong graph nhưng chưa có lịch sử mua hàng.
Kết quả mong đợi: nếu import đủ tốt thì thường không có dòng nào; nếu có thì đây là các user cần kiểm tra lại dữ liệu nguồn.

Tương tự, `No changes, no records` ở câu này có nghĩa là không có `User` nào bị thiếu quan hệ `PURCHASED`, tức dữ liệu đang sạch hơn mong đợi.

6) Tạo quan hệ dẫn xuất `LIKES_CATEGORY` với trọng số

```cypher
MATCH (u:User)-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(c:Category)
WITH u, c, count(*) AS purchase_count
MERGE (u)-[r:LIKES_CATEGORY]->(c)
SET r.purchase_count = purchase_count,
    r.score = purchase_count;
```

Ý nghĩa: suy ra category mà user thích dựa trên số lần mua trong từng category.
Kết quả mong đợi: tạo thêm quan hệ `LIKES_CATEGORY` giữa `User` và `Category`, mỗi quan hệ có `purchase_count` và `score`.

7) Xem top category user yêu thích từ `LIKES_CATEGORY`

```cypher
MATCH (u:User)-[r:LIKES_CATEGORY]->(c:Category)
WHERE toString(u.id) = '1'
RETURN u.id AS user_id, c.name AS category, r.purchase_count AS purchase_count
ORDER BY r.purchase_count DESC
LIMIT 10;
```

Ý nghĩa: kiểm tra nhanh sở thích category của một user cụ thể sau khi đã chạy câu 6.
Kết quả mong đợi: trả về các category mà user `1` thích nhất cùng số lần mua tương ứng.

8) Tạo quan hệ `SIMILAR_TO` giữa user-user theo sản phẩm mua chung

```cypher
MATCH (u1:User)-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(u2:User)
WHERE toString(u1.id) < toString(u2.id)
WITH u1, u2, count(DISTINCT p) AS shared_products
WHERE shared_products >= 1
MERGE (u1)-[r:SIMILAR_TO]->(u2)
SET r.shared_products = shared_products;
```

Ý nghĩa: tạo quan hệ tương đồng giữa hai user nếu họ đã mua cùng sản phẩm.
Kết quả mong đợi: sinh ra các cạnh `SIMILAR_TO` với thuộc tính `shared_products`, biểu diễn số sản phẩm mua chung giữa hai user.

Lưu ý:
- Nếu bạn import ít dữ liệu, điều kiện `shared_products >= 2` có thể không tạo ra bản ghi nào. Với mục đích demo, dùng ngưỡng `>= 1` sẽ ổn định hơn.
- Không dùng `id()` của Neo4j vì hàm này đã bị deprecated. Ở đây nên dùng application id là `u.id`.

9) Xem user tương đồng nhất với một user mục tiêu

```cypher
MATCH (u:User)-[r]-(other:User)
WHERE toString(u.id) = '1'
  AND type(r) = 'SIMILAR_TO'
RETURN other.id AS similar_user_id, r.shared_products AS shared_products
ORDER BY r.shared_products DESC
LIMIT 10;
```

Ý nghĩa: đọc kết quả của câu 8 để xem user nào giống user mục tiêu nhất.
Kết quả mong đợi: trả về danh sách user giống user `1` nhất, xếp theo số sản phẩm mua chung.

10) Tạo quan hệ `CO_PURCHASED_WITH` giữa product-product

```cypher
MATCH (u:User)-[:PURCHASED]->(p1:Product)
MATCH (u)-[:PURCHASED]->(p2:Product)
WHERE toString(p1.id) < toString(p2.id)
WITH p1, p2, count(DISTINCT u) AS co_user_count
WHERE co_user_count >= 1
MERGE (p1)-[r:CO_PURCHASED_WITH]->(p2)
SET r.co_user_count = co_user_count;
```

Ý nghĩa: tạo liên kết giữa hai sản phẩm nếu chúng thường được cùng một user mua chung.
Kết quả mong đợi: sinh ra các cạnh `CO_PURCHASED_WITH` với thuộc tính `co_user_count`, là số user đã mua cả hai sản phẩm.

Nếu câu này không tạo được record thì các câu 11, 12 và một phần câu 17 có thể báo `01N51: Relationship type does not exist` vì trong graph lúc đó chưa hề có quan hệ `CO_PURCHASED_WITH`.

11) Xem cặp sản phẩm thường mua cùng nhau

```cypher
MATCH (p1:Product)-[r]-(p2:Product)
WHERE type(r) = 'CO_PURCHASED_WITH'
RETURN p1.title AS product_1, p2.title AS product_2, r.co_user_count AS co_user_count
ORDER BY r.co_user_count DESC
LIMIT 20;
```

Ý nghĩa: đọc kết quả của câu 10 để xem cặp sản phẩm nào hay đi cùng nhau nhất.
Kết quả mong đợi: trả về hai tên sản phẩm và số user đã mua chung cặp đó.

12) Gợi ý sản phẩm theo quan hệ `CO_PURCHASED_WITH` cho user

```cypher
MATCH (u:User)-[:PURCHASED]->(owned:Product)
WHERE toString(u.id) = '1'
MATCH (owned)-[r]-(cand:Product)
WHERE type(r) = 'CO_PURCHASED_WITH'
  AND NOT (u)-[:PURCHASED]->(cand)
RETURN cand.title AS recommendation, sum(r.co_user_count) AS score
ORDER BY score DESC, recommendation
LIMIT 10;
```

Ý nghĩa: gợi ý sản phẩm mới cho user dựa trên các sản phẩm mà user đã mua và các cặp mua chung.
Kết quả mong đợi: trả về danh sách sản phẩm chưa mua của user `1`, kèm điểm `score` càng cao thì càng đáng gợi ý.

13) Tạo quan hệ `INTERESTED_IN` từ `LIKES_CATEGORY` (top 3 category)

```cypher
MATCH (u:User)-[r:LIKES_CATEGORY]->(c:Category)
WITH u, c, r
ORDER BY u.id, r.score DESC
WITH u, collect(c)[0..3] AS top_categories
UNWIND top_categories AS c
MERGE (u)-[:INTERESTED_IN]->(c);
```

Ý nghĩa: nén sở thích category của mỗi user thành top 3 category nổi bật nhất.
Kết quả mong đợi: mỗi user có tối đa 3 quan hệ `INTERESTED_IN` tới các category quan trọng nhất.

14) Gợi ý nhanh bằng `INTERESTED_IN`

```cypher
MATCH (u:User)-[:INTERESTED_IN]->(c:Category)<-[:BELONGS_TO]-(p:Product)
WHERE toString(u.id) = '1'
  AND NOT (u)-[:PURCHASED]->(p)
RETURN c.name AS category, p.title AS recommendation
ORDER BY category, recommendation
LIMIT 20;
```

Ý nghĩa: gợi ý nhanh sản phẩm theo category mà user quan tâm, không cần tính user-user similarity.
Kết quả mong đợi: trả về tên category và các sản phẩm thuộc category đó mà user `1` chưa mua.

15) Tạo quan hệ `SIMILAR_CATEGORY_TASTE` bằng độ giao category

```cypher
MATCH (u1:User)-[:LIKES_CATEGORY]->(c:Category)<-[:LIKES_CATEGORY]-(u2:User)
WHERE toString(u1.id) < toString(u2.id)
WITH u1, u2, count(DISTINCT c) AS shared_categories
WHERE shared_categories >= 1
MERGE (u1)-[r:SIMILAR_CATEGORY_TASTE]->(u2)
SET r.shared_categories = shared_categories;
```

Ý nghĩa: đo mức giống nhau giữa hai user dựa trên category yêu thích thay vì sản phẩm mua chung.
Kết quả mong đợi: tạo quan hệ `SIMILAR_CATEGORY_TASTE` với thuộc tính `shared_categories`.

16) Xem mạng lưới user tương đồng theo category

```cypher
MATCH (u:User)-[r]-(peer:User)
WHERE toString(u.id) = '1'
  AND type(r) = 'SIMILAR_CATEGORY_TASTE'
RETURN peer.id AS peer_user_id, r.shared_categories AS shared_categories
ORDER BY shared_categories DESC
LIMIT 15;
```

Ý nghĩa: xem user nào có gu category gần nhất với user mục tiêu.
Kết quả mong đợi: trả về các peer user cùng số category giao nhau với user `1`.

17) Kiểm tra các quan hệ dẫn xuất đã tạo

```cypher
MATCH ()-[r]->()
WHERE type(r) IN ['LIKES_CATEGORY', 'SIMILAR_TO', 'CO_PURCHASED_WITH', 'INTERESTED_IN', 'SIMILAR_CATEGORY_TASTE']
RETURN type(r) AS relation_type, count(*) AS total
ORDER BY total DESC;
```

Ý nghĩa: tổng kiểm tra sau khi chạy các lệnh tạo quan hệ dẫn xuất.
Kết quả mong đợi: trả về từng loại relationship mới và số lượng của chúng trong graph.

18) Tìm đường đi recommendation có thể giải thích cho user

```cypher
MATCH p = (u:User)-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(:Category)<-[:BELONGS_TO]-(:Product)<-[:PURCHASED]-(:User)
WHERE toString(u.id) = '1'
RETURN p
LIMIT 5;
```

Ý nghĩa: tìm các path có thể dùng để giải thích recommendation theo kiểu "mua sản phẩm A, cùng category với B, user khác cũng mua B".
Kết quả mong đợi: Neo4j Browser sẽ hiện các path trực quan để bạn demo phần explainability.

19) Kiểm tra quan hệ trùng lặp (nếu có) theo cặp User-Product

```cypher
MATCH (u:User)-[r:PURCHASED]->(p:Product)
WITH u, p, count(r) AS rel_count
WHERE rel_count > 1
RETURN u.id AS user_id, p.id AS product_id, rel_count
ORDER BY rel_count DESC;
```

Ý nghĩa: kiểm tra xem có bị tạo trùng `PURCHASED` giữa cùng một user và product hay không.
Kết quả mong đợi: thông thường không có record; nếu có thì đó là dấu hiệu import hoặc merge chưa sạch.

20) Làm sạch toàn bộ quan hệ dẫn xuất để chạy lại từ đầu

```cypher
MATCH ()-[r]->()
WHERE type(r) IN ['LIKES_CATEGORY', 'SIMILAR_TO', 'CO_PURCHASED_WITH', 'INTERESTED_IN', 'SIMILAR_CATEGORY_TASTE']
DELETE r;
```

Ý nghĩa: xóa toàn bộ quan hệ dẫn xuất để bạn có thể demo lại quá trình tạo chúng từ đầu.
Kết quả mong đợi: các quan hệ gốc `PURCHASED` và `BELONGS_TO` vẫn giữ nguyên, chỉ các relationship suy ra mới bị xóa.

## 10. Kịch bản thuyết trình gợi ý (5-10 phút)

1. Nêu bài toán: recommendation theo hành vi mua hàng.
2. Giải thích vì sao chọn graph thay vì bảng quan hệ thuần.
3. Trình bày nguồn dữ liệu thật từ BigQuery.
4. Mô tả schema `User-Product-Category`.
5. Demo bootstrap dữ liệu.
6. Demo 2 kiểu recommendation hiện tại trong code.
7. Demo thêm các quan hệ dẫn xuất bằng Cypher (mục 9).
8. Chốt giá trị: dễ giải thích, dễ mở rộng, trực quan cho business.

## 11. Điểm mạnh để báo cáo

- Dữ liệu thật, không phải dữ liệu mock.
- Truy vấn recommendation đọc được, giải thích được cho non-tech.
- Có fallback khi collaborative filtering thiếu dữ liệu.
- Có thể mở rộng nhanh bằng cách thêm relationship mới.

## 12. Hạn chế hiện tại

- Chưa có giao diện web trực quan.
- Chưa có signal thời gian (time-decay).
- Chưa kết hợp embedding/ML ranking.
- Chưa có pipeline production (scheduler, monitoring, retry chuẩn).

## 13. Định hướng mở rộng sau demo

1. Bổ sung quan hệ hành vi khác: `VIEWED`, `ADDED_TO_CART`, `WISHLISTED`.
2. Gán trọng số theo thời gian mua gần đây.
3. Kết hợp scoring graph + embedding để tăng độ chính xác.
4. Đánh giá bằng metric offline (Precision@K, Recall@K, Coverage).

## 14. Kết luận ngắn gọn để chốt slide

> Dự án đã chứng minh được luồng BigQuery -> Neo4j -> Recommendation chạy tốt trên dữ liệu thật, tận dụng mô hình quan hệ để tạo gợi ý trực quan, có thể giải thích và mở rộng nhanh cho các bài toán recommendation thực tế.
