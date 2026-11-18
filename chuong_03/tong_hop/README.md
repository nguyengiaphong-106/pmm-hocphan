\# Bài tập Chương 3 - Flask Student Score API



\## 1. Mô tả



Ứng dụng Flask quản lý sinh viên và điểm môn học.



Các chức năng chính:



\* Hiển thị danh sách sinh viên.

\* Xem thông tin chi tiết sinh viên.

\* Tìm kiếm sinh viên.

\* Lọc sinh viên theo lớp và điểm trung bình.

\* API lấy danh sách sinh viên.

\* API lấy thông tin chi tiết sinh viên.

\* API GET/PUT/DELETE điểm môn học.

\* Xuất điểm của một sinh viên ra file CSV.

\* Redirect từ `/sv/<mssv>` sang `/students/<mssv>`.

\* Xử lý lỗi 404, 405 và 400 cho API.



\## 2. Cài đặt và chạy chương trình



Tạo và kích hoạt môi trường ảo:



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



Cài đặt thư viện:



```powershell

pip install -r requirements.txt

```



Chạy Flask:



```powershell

flask --app sodiem run

```



Ứng dụng chạy mặc định tại:



```text

http://127.0.0.1:5000

```



\## 3. Danh sách routes



Kết quả của lệnh:



```powershell

flask --app sodiem routes

```



```text

Endpoint            Methods           Rule

\------------------  ----------------  ------------------------------------

api\_student\_detail  GET               /api/students/<mssv>

api\_students        GET               /api/students

export\_student      GET               /students/<mssv>/export

index               GET               /

old\_student\_url     GET               /sv/<mssv>

score\_api           DELETE, GET, PUT  /api/students/<mssv>/scores/<course>

search              GET               /search

static              GET               /static/<path:filename>

student\_detail      GET               /students/<mssv>

students            GET               /students

```



\## 4. Kết quả kiểm thử



\### 4.1. Lấy thông tin sinh viên



```powershell

curl.exe -i "http://127.0.0.1:5000/api/students/23T1020001"

```



Kết quả:



```text

HTTP/1.1 200 OK

Content-Type: application/json



{"average":8.17,"ho\_ten":"Nguyễn Văn An","lop":"K47A","mssv":"23T1020001","rank":"Khá","scores":{"CSDL":7.0,"MMT":9.0,"PMMNM":8.5}}

```



\### 4.2. Lấy điểm một môn



```powershell

curl.exe -i "http://127.0.0.1:5000/api/students/23T1020001/scores/PMMNM"

```



Kết quả:



```text

HTTP/1.1 200 OK



{"course":"PMMNM","mssv":"23T1020001","score":8.5}

```



\### 4.3. Cập nhật điểm môn học



```powershell

curl.exe -i -X PUT "http://127.0.0.1:5000/api/students/23T1020001/scores/PMMNM" -H "Content-Type: application/json" --data-binary '{\\"score\\":9.0}'

```



Kết quả:



```text

HTTP/1.1 200 OK



{"average":8.33,"course":"PMMNM","mssv":"23T1020001","score":9.0}

```



\### 4.4. Thêm môn học mới



```powershell

curl.exe -i -X PUT "http://127.0.0.1:5000/api/students/23T1020001/scores/ABC" -H "Content-Type: application/json" --data-binary '{\\"score\\":8.0}'

```



Kết quả:



```text

HTTP/1.1 201 CREATED

Content-Type: application/json

Location: /api/students/23T1020001/scores/ABC



{"average":8.25,"course":"ABC","mssv":"23T1020001","score":8.0}

```



\### 4.5. Xóa điểm môn học



```powershell

curl.exe -i -X DELETE "http://127.0.0.1:5000/api/students/23T1020001/scores/ABC"

```



Kết quả:



```text

HTTP/1.1 204 NO CONTENT

```



\### 4.6. Sinh viên không tồn tại



```powershell

curl.exe -i "http://127.0.0.1:5000/api/students/9999999999"

```



Kết quả:



```text

HTTP/1.1 404 NOT FOUND

Content-Type: application/json



{"detail":"Không có sinh viên với MSSV = 9999999999.","error":"not\_found"}

```



\### 4.7. Phương thức HTTP không được phép



```powershell

curl.exe -i -X POST "http://127.0.0.1:5000/api/students/23T1020001/scores/PMMNM"

```



Kết quả:



```text

HTTP/1.1 405 METHOD NOT ALLOWED

Content-Type: application/json



{"detail":"Phương thức HTTP không được phép","error":"method\_not\_allowed"}

```



\### 4.8. Request thiếu `score`



```powershell

curl.exe -i -X PUT "http://127.0.0.1:5000/api/students/23T1020001/scores/PMMNM" -H "Content-Type: application/json" --data-binary '{}'

```



Kết quả:



```text

HTTP/1.1 400 BAD REQUEST

Content-Type: application/json



{"detail":"Thiếu score","error":"bad\_request"}

```



\### 4.9. Trang không tồn tại



```powershell

curl.exe -i "http://127.0.0.1:5000/abc"

```



Kết quả:



```text

HTTP/1.1 404 NOT FOUND

Content-Type: text/html; charset=utf-8

```



Trang trả về HTML với tiêu đề:



```text

404 - Không tìm thấy

```



\### 4.10. Xuất CSV



```powershell

curl.exe -i "http://127.0.0.1:5000/students/23T1020001/export"

```



Kết quả:



```text

HTTP/1.1 200 OK

Content-Type: text/csv; charset=utf-8

Content-Disposition: attachment; filename=diem\_23T1020001.csv

```



Nội dung CSV:



```text

MSSV,Họ tên,Lớp,Môn học,Điểm

23T1020001,Nguyễn Văn An,K47A,PMMNM,8.5

23T1020001,Nguyễn Văn An,K47A,CSDL,7.0

23T1020001,Nguyễn Văn An,K47A,MMT,9.0

```



\## 5. Câu hỏi



\### Câu 1. Tại sao redirect thường dùng 301/302 còn tạo mới lại dùng 201?



`301` và `302` là các mã trạng thái HTTP dùng để thông báo rằng tài nguyên được yêu cầu có địa chỉ khác hoặc cần chuyển hướng sang URL khác.



Trong khi đó, `201 Created` được sử dụng khi server đã tạo thành công một tài nguyên mới. Trong API PUT của bài này, khi thêm một môn học chưa tồn tại, server trả về `201 Created` và header `Location` chứa URL của tài nguyên mới.



\### Câu 2. Dữ liệu có tồn tại sau khi tắt và chạy lại Flask không?



Không.



Dữ liệu trong bài được lưu trực tiếp trong biến `STUDENTS` ở bộ nhớ của chương trình. Khi Flask dừng, dữ liệu thay đổi trong bộ nhớ sẽ mất. Khi chạy lại Flask, dữ liệu được nạp lại từ giá trị ban đầu của `STUDENTS`.



Muốn dữ liệu vẫn tồn tại sau khi khởi động lại ứng dụng thì cần lưu vào cơ sở dữ liệu hoặc một file dữ liệu bên ngoài.

## 6. Trạng thái

Các API và route chính đã được kiểm thử bằng curl trên Flask development server.

## 7. Cấu trúc project

- .gitignore: loại trừ môi trường ảo và file tạm.
- requirements.txt: danh sách thư viện Python cần thiết.
- sodiem.py: mã nguồn Flask.
- README.md: hướng dẫn chạy, routes và kết quả kiểm thử.
