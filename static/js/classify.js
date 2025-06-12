const uploadArea = document.getElementById('uploadArea');
const uploadInput = document.getElementById('uploadInput');
const imagePreview = document.getElementById('imagePreview');
const previewImage = document.getElementById('previewImage');
const analyzeBtn = document.getElementById('analyzeBtn');
const loading = document.getElementById('loading');
const placeholderText = document.getElementById('placeholderText');
const resultContent = document.getElementById('resultContent');
const resultImage = document.getElementById('resultImage');
const breedName = document.getElementById('breedName');
const confidencePercent = document.getElementById('confidencePercent');
const confidenceFill = document.getElementById('confidenceFill');

// Upload Area Events
uploadArea.addEventListener('click', () => uploadInput.click());
uploadArea.addEventListener('dragover', handleDragOver);
uploadArea.addEventListener('dragleave', handleDragLeave);
uploadArea.addEventListener('drop', handleDrop);
uploadInput.addEventListener('change', handleFileSelect);
analyzeBtn.addEventListener('click', analyzeImage);

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}
function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
}
function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Vui lòng chọn file hình ảnh!');
        return;
    }
    if (file.size > 5 * 1024 * 1024) { // 5MB
        alert('File quá lớn! Vui lòng chọn file nhỏ hơn 5MB.');
        return;
    }
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        imagePreview.style.display = 'none';  // Ẩn xem trước

        // Hiện ảnh luôn ở khu vực kết quả
        resultImage.src = e.target.result;
        resultImage.style.display = 'block';

        placeholderText.style.display = 'none';
        resultContent.classList.add('show');
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

function analyzeImage() {
    loading.classList.add('show');
    placeholderText.style.display = 'none';
    resultContent.classList.remove('show');
    analyzeBtn.disabled = true;

    const file = uploadInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('/classify', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            throw new Error(data.error);
        }
        loading.classList.remove('show');
        breedName.textContent = data.breed_vi;
        confidencePercent.textContent = (data.confidence * 100).toFixed(2) + '%';
        confidenceFill.style.width = (data.confidence * 100).toFixed(2) + '%';
        resultContent.classList.add('show');
        analyzeBtn.disabled = false;
        document.getElementById('retryBtn').style.display = 'block';    // Hiện nút phân loại lại
        feedbackButtons.style.display = 'flex';
        feedbackMessage.style.display = 'none';
    })
    .catch(error => {
        console.error('Lỗi:', error);
        loading.classList.remove('show');
        alert('Đã xảy ra lỗi: ' + error.message);
        analyzeBtn.disabled = false;
    });
}

// Add smooth scrolling for better UX
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

const retryBtn = document.getElementById('retryBtn');
retryBtn.addEventListener('click', () => {
    uploadInput.value = '';    // Reset file input
    // Ẩn ảnh kết quả và ảnh preview
    resultImage.src = '';
    resultImage.style.display = 'none';
    previewImage.src = '';
    imagePreview.style.display = 'none';
    // Ẩn kết quả và loading
    resultContent.classList.remove('show');
    loading.classList.remove('show');
    placeholderText.style.display = 'block';    // Hiện lại placeholder
    // Reset kết quả text và thanh độ tin cậy
    breedName.textContent = '';
    confidencePercent.textContent = '0%';
    confidenceFill.style.width = '0%';
    analyzeBtn.disabled = true;    // Disable nút "Phân loại ngay"
    retryBtn.style.display = 'none';    // Ẩn lại nút phân loại lại
});

const feedbackButtons = document.getElementById('feedbackButtons');
const correctBtn = document.getElementById('correctBtn');
const wrongBtn = document.getElementById('wrongBtn');
const feedbackMessage = document.getElementById('feedbackMessage');

correctBtn.addEventListener('click', () => {
    feedbackMessage.textContent = '🎉 Cảm ơn bạn đã xác nhận kết quả đúng!';
    feedbackMessage.style.display = 'block';
    feedbackButtons.style.display = 'none';
});

wrongBtn.addEventListener('click', () => {
    feedbackMessage.textContent = '😔 Cảm ơn bạn, chúng tôi sẽ cải thiện mô hình.';
    feedbackMessage.style.display = 'block';
    feedbackButtons.style.display = 'none';
});

