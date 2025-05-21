function updateImage() {
    fetch('/processed-image')
        .then(response => response.json())
        .then(data => {
            console.log("Ảnh đã nhận diện mới nhất:", data.image_name);
            if (data.image_name !== "") {
                let imgElement = document.getElementById("latest-image");
                imgElement.src = "/uploads/" + data.image_name + "?t=" + new Date().getTime(); // Tránh cache
                document.getElementById("image-container").classList.remove("hidden");
            }
        })
        .catch(error => console.error('Lỗi khi tải ảnh đã nhận diện:', error));
}

function updateLogs() {
    fetch('/access_control')
        .then(response => response.json())
        .then(data => {
            console.log("Dữ liệu logs nhận được:", data);  // Debug
            let tableBody = document.getElementById('log-table-body');
            tableBody.innerHTML = '';     // Xóa dữ liệu cũ
            data.forEach(log => {
                let row = document.createElement("tr");
                row.innerHTML = `
                    <td>${log.id}</td>
                    <td>${log.time}</td>
                    <td>${log.breed}</td>
                    <td><img src="/uploads/${log.image_name}" class="thumbnail" onclick="showImage('/uploads/${log.image_name}')"></td>
                    `;
                //tableBody.innerHTML += row;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.log('Lỗi khi tải logs: ', error));
}

// Hàm hiển thị ảnh lớn khi click vào ảnh thu nhỏ
function showImage(imageSrc) {
    let modal = document.getElementById("imageModal");
    let modalImg = document.getElementById("fullImage");

    modal.style.display = "block";
    modalImg.src = imageSrc + "?t=" + new Date().getTime(); // Tránh cache

    let closeBtn = document.querySelector(".close");
    closeBtn.onclick = function () {
        modal.style.display = "none";
    };
    modal.onclick = function () {
        modal.style.display = "none";
    };
}

function updateChart() {
    fetch('/stats')
        .then(response => response.json())
        .then(data => {
            console.log("📊 Dữ liệu thống kê:", data); // Debug
            let breeds = Object.keys(data);
            let counts = Object.values(data);

            let ctx = document.getElementById("breedChart").getContext("2d");
            if (window.myChart) {
                window.myChart.destroy();   // Xóa biểu đồ cũ nếu có
            }
            window.myChart = new Chart(ctx, {
                type: "bar",
                data: {
                    labels: breeds,
                    datasets: [{
                        label: "Số lượng",
                        data: counts,
                        backgroundColor: "rgba(75, 192, 192, 0.6)",
                        borderColor: "rgba(75, 192, 192, 1)",
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        })
        .catch(error => console.error("Lỗi khi tải dữ liệu thống kê:", error));
}

// Khi chọn ảnh, hiển thị ảnh ngay lập tức trước khi tải lên
//document.getElementById('uploadInput').addEventListener('change', function(event) {
//    let file = event.target.files[0];
//   if (file) {
//        let imageUrl = URL.createObjectURL(file);
//        document.getElementById('uploadedImage').src = imageUrl;
//        document.getElementById('uploadedImage').style.display = 'block';
//    }
//});

function uploadImage() {
    let input = document.getElementById('uploadInput');
    if (input.files.length === 0) {
        alert('Vui lòng chọn ảnh!');
        return;
    }
    let file = input.files[0];
    let formData = new FormData();
    formData.append("file", file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Hiển thị ảnh sau khi tải lên thành công
            document.getElementById('uploadedImage').src = `/uploads/${data.image_name}`;
            document.getElementById('uploadedImage').style.display = 'block';
            // Hiển thị nút phân loại sau khi upload xong
            document.getElementById('classifyButton').style.display = 'inline-block';
            document.getElementById('classifyButton').dataset.imageName = data.image_name;
        } else {
            alert('Tải ảnh thất bại!' + data.error);
            return;
        }
    })
    .catch(error => console.error('Lỗi khi tải ảnh:', error));
}

function classifyImage() {
    let imageName = document.getElementById('classifyButton').dataset.imageName;
    if (!imageName) {
        alert("Lỗi: Không tìm thấy ảnh đã tải lên!");
        return;
    }

    fetch('/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_name: imageName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("Phân loại thành công:", data.breed);
            document.getElementById('classificationResult').innerText = "Giống: " + data.breed;
            updateLogs();
        } else {
            alert("Phân loại thất bại!" + data.error);
            return;
        }
    })
    .catch(error => console.error('Lỗi khi phân loại ảnh: ', error));
}

function resetDatabase() {
    if (confirm("Bạn có chắc chắn muốn xóa toàn bộ dữ liệu?")) {
        fetch('/reset_database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                location.reload(); // Làm mới trang sau khi reset
            } else {
                alert("Lỗi khi reset database: " + data.message);
                return;
            }
        })
        .catch(error => console.error('Lỗi kết nối đến server:', error));
    }
}

// Cập nhật ảnh và log mỗi 5 giây
setInterval(updateImage, 5000);
setInterval(updateLogs, 5000);
// Cập nhật biểu đồ mỗi 5 giây
setInterval(updateChart, 5000);
