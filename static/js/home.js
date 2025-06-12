// Menu toggle for mobile
        document.querySelector('.menu-toggle').addEventListener('click', function() {
            document.querySelector('.nav-links').classList.toggle('active');
        });

        // Breed Carousel
        const breedGrid = document.querySelector('.breed-grid');
        const prevBtns = document.querySelectorAll('.prev-btn');
        const nextBtns = document.querySelectorAll('.next-btn');
        const breedCards = document.querySelectorAll('.breed-card:not(.breed-card.clone)'); // Chỉ chọn card gốc
        let currentPosition = 0;
        const cardsPerView = 3;
        let autoPlayInterval;
        const autoPlayDelay = 10000; // 10 giây
        let isAnimating = false;

        // Clone các card để tạo hiệu ứng infinite
        function cloneCards() {
            const firstCard = breedCards[0];
            const lastCard = breedCards[breedCards.length - 1];

            // Clone card đầu và cuối để tạo hiệu ứng vô hạn
            const firstClone = firstCard.cloneNode(true);
            firstClone.classList.add('clone');
            breedGrid.appendChild(firstClone);

            const lastClone = lastCard.cloneNode(true);
            lastClone.classList.add('clone');
            breedGrid.insertBefore(lastClone, breedGrid.firstChild);
        }
        cloneCards();

        // Cập nhật lại danh sách card sau khi clone
        const allCards = document.querySelectorAll('.breed-card');
        const totalCards = breedCards.length;       // Sử dụng số lượng card gốc

        // Đặt vị trí ban đầu là 1 (vì đã clone card đầu)
        currentPosition = 1;

        function updateCarousel() {
            const cardWidth = 350; // Fixed width cho mỗi card
            const gap = 40; // 2.5rem = 40px
            const moveDistance = cardWidth + gap;

            breedGrid.style.transform = `translateX(${-currentPosition * moveDistance}px)`;

<!--            // Cập nhật trạng thái nút-->
<!--            prevBtns.forEach(btn => btn.disabled = currentPosition <= 0);-->
<!--            nextBtns.forEach(btn => btn.disabled = currentPosition >= totalCards - 3);-->
            // Không disable nút nào vì có infinite scroll
            prevBtns.forEach(btn => btn.disabled = false);
            nextBtns.forEach(btn => btn.disabled = false);
        }

        function moveToPosition(position) {
            currentPosition = position;
            updateCarousel();

            // Xử lý hiệu ứng vô hạn
            const containerWidth = document.querySelector('.breed-carousel').offsetWidth;
            const cardWidth = (containerWidth - 5 * 40) / 3;
            const moveDistance = 390; // 350px card + 40px gap

            // Nếu đang ở card clone đầu tiên (ảo), nhảy đến card thật cuối cùng
            if (currentPosition <= 0) {
                setTimeout(() => {
                    breedGrid.style.transition = 'none';
                    currentPosition = totalCards;
                    breedGrid.style.transform = `translateX(${-currentPosition * moveDistance}px)`;
                    setTimeout(() => {
                        breedGrid.style.transition = 'transform 0.5s ease';
                    }, 50);
                }, 500);
            }

            // Nếu đang ở card clone cuối cùng (ảo), nhảy đến card thật đầu tiên
            if (currentPosition >= totalCards) {
                setTimeout(() => {
                    breedGrid.style.transition = 'none';
                    currentPosition = 1;
                    breedGrid.style.transform = `translateX(${-currentPosition * moveDistance}px)`;
                    setTimeout(() => {
                        breedGrid.style.transition = 'transform 0.5s ease';
                    }, 50);
                }, 500);
            }
        }

        function movePrev() {
            moveToPosition(currentPosition - 1);
            resetAutoPlay();
        }
        function moveNext() {
            moveToPosition(currentPosition + 1);
            resetAutoPlay();
        }

        // Gán sự kiện cho tất cả các nút prev/next
        prevBtns.forEach(btn => btn.addEventListener('click', movePrev));
        nextBtns.forEach(btn => btn.addEventListener('click', moveNext));

        // Auto-play
        function startAutoPlay() {
            autoPlayInterval = setInterval(moveNext, autoPlayDelay);
        }
        function stopAutoPlay() {
            clearInterval(autoPlayInterval);
        }
        function resetAutoPlay() {
            stopAutoPlay();
            startAutoPlay();
        }

        // Dừng auto-play khi hover vào carousel
        document.querySelector('.breed-carousel').addEventListener('mouseenter', stopAutoPlay);
        document.querySelector('.breed-carousel').addEventListener('mouseleave', startAutoPlay);

        // Khởi tạo carousel
        updateCarousel();
        startAutoPlay();

        // Cập nhật khi resize window
        window.addEventListener('resize', updateCarousel);

        // Enhanced hover effects
        document.querySelectorAll('.breed-card, .feature-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-15px) scale(1.02)';
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });

        function openPopup(popupId) {
            const popup = document.getElementById(popupId);
            if (popup) {
                popup.style.display = 'flex';
                popup.style.opacity = '0';
                popup.style.transition = 'opacity 0.3s ease';
                requestAnimationFrame(() => {
                    popup.style.opacity = '1';
                });
                document.body.style.overflow = 'hidden';
            }
        }

        function closePopup(popupId) {
            const popup = document.getElementById(popupId);
            if (popup) {
                popup.style.opacity = '0';
                popup.style.transition = 'opacity 0.3s ease';
                setTimeout(() => {
                    popup.style.display = 'none';
                    document.body.style.overflow = 'auto';
                }, 300);
            }
        }

        function formatBreedFilename(breedName) {
            return breedName.toLowerCase().replace(/\s+/g, '-');
        }
        function showBreedDetail(breedName) {
            const popup = document.getElementById('breedPopup');
            const breedNameElement = document.getElementById('popupBreedName');
            const imageElement = document.getElementById('popupBreedImage');
            const infoContainer = document.querySelector('.breed-info');
            const fileName = formatBreedFilename(breedName);

            breedNameElement.textContent = breedName;
            imageElement.src = `static/images/${breedName.toLowerCase().replace(/ /g, "-")}.jpg`;
            imageElement.alt = breedName;

            fetch(`static/data/${fileName}.txt`)
                .then(response => {
                    if (!response.ok) throw new Error("Không tìm thấy thông tin");
                    return response.text();
                })
                .then(text => {
                    infoContainer.innerHTML = `<p>${text.replace(/\n/g, '<br>')}</p>`;
                    openPopup('breedPopup');
                })
                .catch(err => {
                    infoContainer.innerHTML = `<p>Không có thông tin cho giống "${breedName}".</p>`;
                    openPopup('breedPopup');
                });
        }
        function closeBreedDetail() {
            console.log("Đóng popup");
            closePopup('breedPopup');
        }

        // Đóng popup khi click bên ngoài nội dung
        document.addEventListener('DOMContentLoaded', function () {
            document.getElementById('breedPopup').addEventListener('click', function(e) {
                if (e.target === this) {
                    closePopup('breedPopup');
                }
            });
        });

        // Navbar background change on scroll
        window.addEventListener('scroll', function() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 50) {
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
                navbar.style.boxShadow = '0 10px 40px rgba(0,0,0,0.15)';
            } else {
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                navbar.style.boxShadow = '0 8px 32px rgba(0,0,0,0.1)';
            }
        });

        // Floating animation for hero image
        document.addEventListener('DOMContentLoaded', function() {
            const heroImage = document.querySelector('.hero-image img');
            if (heroImage) {
                let floatDirection = 1;

                setInterval(() => {
                    const currentTransform = heroImage.style.transform || 'translateY(0px)';
                    const currentY = parseInt(currentTransform.match(/-?\d+/) || [0])[0];

                    if (currentY >= 10) floatDirection = -1;
                    if (currentY <= -10) floatDirection = 1;

                    heroImage.style.transform = `translateY(${currentY + (floatDirection * 0.5)}px)`;
                }, 50);
            }
        });