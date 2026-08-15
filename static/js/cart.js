// central cart and wishlist management system

// 0. Initialize Catalog if not present
const initialCatalog = [
    { id: 1, title: "Atomic Habits", author: "James Clear", price: 499, img: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300", condition: "new", description: "An easy & proven way to build good habits & break bad ones. Tiny Changes, Remarkable Results.", approved: true },
    { id: 2, title: "Deep Work", author: "Cal Newport", price: 399, img: "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=300", condition: "new", description: "Rules for Focused Success in a Distracted World. Master difficult skills quickly and produce better results in less time.", approved: true },
    { id: 3, title: "Rich Dad Poor Dad", author: "Robert Kiyosaki", price: 299, img: "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=300", condition: "new", description: "What the Rich Teach Their Kids About Money That the Poor and Middle Class Do Not!", approved: true },
    { id: 4, title: "The Psychology of Money", author: "Morgan Housel", price: 599, img: "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=300", condition: "new", description: "Timeless lessons on wealth, greed, and happiness. Doing well with money isn't necessarily about what you know. It's about how you behave.", approved: true },
    { id: 5, title: "The Alchemist", author: "Paulo Coelho", price: 149, img: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=300", condition: "pre-loved", description: "A beautiful story about following your dreams. Highly inspiring fable about a shepherd boy who travels in search of worldly treasures.", approved: true },
    { id: 6, title: "Zero to One", author: "Peter Thiel", price: 199, img: "https://images.unsplash.com/photo-1531988042231-d39a9cc12a9a?w=300", condition: "pre-loved", description: "Notes on Startups, or How to Build the Future. Learn how to discover new ways of creating value to go from 0 to 1.", approved: true },
    { id: 7, title: "Thinking, Fast and Slow", author: "Daniel Kahneman", price: 249, img: "https://images.unsplash.com/photo-1495640388908-05fa85288e61?w=300", condition: "pre-loved", description: "A deep exploration of the two systems that drive our way of thinking: System 1 (fast/intuitive) and System 2 (slow/logical).", approved: true },
    { id: 8, title: "Steve Jobs", author: "Walter Isaacson", price: 299, img: "https://images.unsplash.com/photo-1541963463532-d68292c34b19?w=300", condition: "pre-loved", description: "The exclusive biography of the creative entrepreneur who revolutionized the technology industry. Based on more than forty interviews.", approved: true }
];

if (!localStorage.getItem('bookbazar_catalog')) {
    localStorage.setItem('bookbazar_catalog', JSON.stringify(initialCatalog));
}

function getCatalog() {
    return JSON.parse(localStorage.getItem('bookbazar_catalog')) || initialCatalog;
}

function saveCatalog(catalog) {
    localStorage.setItem('bookbazar_catalog', JSON.stringify(catalog));
}
function addBookToCatalog(book) {
    const catalog = getCatalog();
    book.approved = false; // Force default pending approval status
    catalog.push(book);
    saveCatalog(catalog);
    
    // Sync to server
    fetch('/api/book/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(book)
    }).then(res => res.json()).then(data => {
        if (data.error) console.error("Sync failed:", data.error);
    });
}
// 1. Storage Helpers
function getCart() {
    return JSON.parse(localStorage.getItem('bookbazar_cart')) || [];
}

function saveCart(cart) {
    localStorage.setItem('bookbazar_cart', JSON.stringify(cart));
    updateBadges();
    // Dispatch custom event for real-time notification across components
    window.dispatchEvent(new Event('cartUpdated'));
}

function getWishlist() {
    return JSON.parse(localStorage.getItem('bookbazar_wishlist')) || [];
}

function saveWishlist(wishlist) {
    localStorage.setItem('bookbazar_wishlist', JSON.stringify(wishlist));
    updateBadges();
    window.dispatchEvent(new Event('wishlistUpdated'));
}

// 2. Badge UI updates
function updateBadges() {
    const cart = getCart();
    const wishlist = getWishlist();

    const cartCount = cart.reduce((total, item) => total + item.quantity, 0);
    const wishlistCount = wishlist.length;

    // Navbar Badges
    const cartBadge = document.getElementById('cart-badge');
    const wishlistBadge = document.getElementById('wishlist-badge');

    if (cartBadge) {
        if (cartCount > 0) {
            cartBadge.textContent = cartCount;
            cartBadge.style.display = 'inline-block';
        } else {
            cartBadge.style.display = 'none';
        }
    }

    if (wishlistBadge) {
        if (wishlistCount > 0) {
            wishlistBadge.textContent = wishlistCount;
            wishlistBadge.style.display = 'inline-block';
        } else {
            wishlistBadge.style.display = 'none';
        }
    }

    // Sidebar Badges (Dashboard)
    const sidebarCartBadge = document.getElementById('sidebar-cart-badge');
    const sidebarWishlistBadge = document.getElementById('sidebar-wishlist-badge');

    if (sidebarCartBadge) {
        if (cartCount > 0) {
            sidebarCartBadge.textContent = cartCount;
            sidebarCartBadge.style.display = 'inline-block';
        } else {
            sidebarCartBadge.style.display = 'none';
        }
    }

    if (sidebarWishlistBadge) {
        if (wishlistCount > 0) {
            sidebarWishlistBadge.textContent = wishlistCount;
            sidebarWishlistBadge.style.display = 'inline-block';
        } else {
            sidebarWishlistBadge.style.display = 'none';
        }
    }
}

// 3. Cart & Wishlist Actions
function addToCart(book) {
    let cart = getCart();
    const existingIndex = cart.findIndex(item => item.id == book.id);
    if (existingIndex > -1) {
        cart[existingIndex].quantity += 1;
    } else {
        cart.push({
            id: book.id,
            title: book.title,
            price: Number(book.price),
            img: book.img,
            author: book.author,
            quantity: 1
        });
    }
    saveCart(cart);
    showNotification(`"${book.title}" added to Cart!`, 'success');

    // Sync to server
    fetch('/api/cart/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ book_id: book.id })
    });
}

function updateCartQuantity(bookId, delta) {
    let cart = getCart();
    const index = cart.findIndex(item => item.id == bookId);
    if (index > -1) {
        cart[index].quantity += delta;
        if (cart[index].quantity <= 0) {
            cart.splice(index, 1);
        }
        saveCart(cart);
    }
    
    // Sync to server
    fetch('/api/cart/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ book_id: bookId, delta: delta })
    });
}

// Separate function for direct removal to trigger notifications
function removeFromCart(bookId) {
    let cart = getCart();
    const item = cart.find(i => i.id == bookId);
    cart = cart.filter(i => i.id != bookId);
    saveCart(cart);
    if (item) {
        showNotification(`"${item.title}" removed from Cart`, 'info');
    }
    
    // Sync to server
    fetch('/api/cart/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ book_id: bookId })
    });
}

function addToWishlist(book) {
    let wishlist = getWishlist();
    const exists = wishlist.some(item => item.id == book.id);
    if (!exists) {
        wishlist.push({
            id: book.id,
            title: book.title,
            price: Number(book.price),
            img: book.img,
            author: book.author
        });
        saveWishlist(wishlist);
        showNotification(`"${book.title}" added to Wishlist!`, 'success');
        
        // Sync to server
        fetch('/api/wishlist/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ book_id: book.id })
        });
    } else {
        showNotification(`"${book.title}" is already in your Wishlist!`, 'info');
    }
}

function removeFromWishlist(bookId) {
    let wishlist = getWishlist();
    const item = wishlist.find(i => i.id == bookId);
    wishlist = wishlist.filter(i => i.id != bookId);
    saveWishlist(wishlist);
    if (item) {
        showNotification(`"${item.title}" removed from Wishlist`, 'info');
    }
    
    // Sync to server
    fetch('/api/wishlist/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ book_id: bookId })
    });
}


// Notification Helper
function showNotification(message, type = 'success') {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.bottom = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'success' ? 'success' : type === 'info' ? 'info' : 'danger'} alert-dismissible fade show shadow-lg`;
    toast.style.minWidth = '250px';
    toast.style.borderRadius = '12px';
    toast.style.border = 'none';
    toast.style.background = type === 'success' ? '#10B981' : type === 'info' ? '#3B82F6' : '#EF4444';
    toast.style.color = '#fff';
    toast.innerHTML = `
        <div class="d-flex align-items-center justify-content-between gap-3">
            <span class="fw-bold">${message}</span>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(toast);
        bsAlert.close();
    }, 3000);
}

// 4. Page Rendering functions
function renderCartPage() {
    const container = document.getElementById('cart-items-container');
    const summaryCol = document.getElementById('cart-summary-col');
    if (!container) return;

    const cart = getCart();

    if (cart.length === 0) {
        container.innerHTML = `
            <div class="card border-0 shadow-sm rounded-4 p-5 text-center" style="background: #111114; color: white;">
                <i class="bi bi-cart-x text-muted" style="font-size: 4rem;"></i>
                <h3 class="fw-bold mt-3">Your Cart is Empty</h3>
                <p class="text-muted">You haven't added any books to your cart yet.</p>
                <a href="/books" class="btn btn-primary rounded-pill px-4 py-2 mt-2">Browse Books</a>
            </div>
        `;
        if (summaryCol) {
            summaryCol.style.display = 'none';
        }
        const cartGrid = container.closest('.row');
        if (cartGrid) {
            container.className = 'col-lg-12';
        }
        return;
    }

    if (summaryCol) {
        summaryCol.style.display = 'block';
    }
    container.className = 'col-lg-8';

    let html = '';
    let subtotal = 0;

    cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        subtotal += itemTotal;

        html += `
            <div class="card border-0 shadow-sm rounded-4 p-4 mb-3" style="background: #111114; color: white;">
                <div class="row align-items-center">
                    <div class="col-md-2 text-center">
                        <img src="${item.img}" class="img-fluid rounded" style="height: 100px; object-fit: cover;" alt="${item.title}">
                    </div>
                    <div class="col-md-4">
                        <h5 class="fw-bold text-white">${item.title}</h5>
                        <p class="text-muted mb-1">${item.author || ''}</p>
                        <span class="fw-bold text-primary">₹${item.price}</span>
                    </div>
                    <div class="col-md-3 text-center">
                        <div class="btn-group align-items-center">
                            <button class="btn btn-outline-danger btn-qty-dec px-2 py-1" data-id="${item.id}" style="color: #ef4444 !important; border-color: rgba(239, 68, 68, 0.4) !important;">
                                <i class="bi bi-dash"></i>
                            </button>
                            <span class="px-3 fw-bold text-white" style="font-size: 1.1rem; min-width: 40px; display: inline-block; text-align: center;">
                                ${item.quantity}
                            </span>
                            <button class="btn btn-outline-success btn-qty-inc px-2 py-1" data-id="${item.id}" style="color: #10b981 !important; border-color: rgba(16, 185, 129, 0.4) !important;">
                                <i class="bi bi-plus"></i>
                            </button>
                        </div>
                    </div>
                    <div class="col-md-3 text-end">
                        <h5 class="text-primary fw-bold">₹${itemTotal}</h5>
                        <button class="btn btn-outline-danger btn-sm mt-2 btn-remove-cart" data-id="${item.id}">
                            <i class="bi bi-trash"></i> Remove
                        </button>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;

    const subtotalEl = document.getElementById('cart-subtotal');
    const totalEl = document.getElementById('cart-total');

    if (subtotalEl) subtotalEl.textContent = `₹${subtotal}`;
    if (totalEl) totalEl.textContent = `₹${subtotal}`;

    // Rebind handlers
    document.querySelectorAll('.btn-qty-dec').forEach(btn => {
        btn.addEventListener('click', () => {
            updateCartQuantity(btn.dataset.id, -1);
            renderCartPage();
        });
    });

    document.querySelectorAll('.btn-qty-inc').forEach(btn => {
        btn.addEventListener('click', () => {
            updateCartQuantity(btn.dataset.id, 1);
            renderCartPage();
        });
    });

    document.querySelectorAll('.btn-remove-cart').forEach(btn => {
        btn.addEventListener('click', () => {
            removeFromCart(btn.dataset.id);
            renderCartPage();
        });
    });
}

function renderWishlistPage() {
    const container = document.getElementById('wishlist-container');
    if (!container) return;

    const wishlist = getWishlist();

    if (wishlist.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="card border-0 shadow-sm rounded-4 p-5 text-center" style="background: #111114; color: white;">
                    <i class="bi bi-heart-break text-muted" style="font-size: 4rem;"></i>
                    <h3 class="fw-bold mt-3">Your Wishlist is Empty</h3>
                    <p class="text-muted">Explore books and add your favorites to the wishlist.</p>
                    <a href="/books" class="btn btn-primary rounded-pill px-4 py-2 mt-2">Explore Books</a>
                </div>
            </div>
        `;
        return;
    }

    let html = '';
    wishlist.forEach(item => {
        html += `
            <div class="col-md-4">
                <div class="card h-100 border-0 shadow-sm rounded-4 overflow-hidden" style="background: #111114; color: white;">
                    <img src="${item.img}" class="card-img-top" alt="${item.title}" style="height: 250px; object-fit: cover;">
                    <div class="card-body p-4 d-flex flex-column">
                        <h5 class="fw-bold mb-1 text-white">${item.title}</h5>
                        <p class="text-muted small mb-3">${item.author || ''}</p>
                        <div class="d-flex justify-content-between align-items-center mt-auto">
                            <span class="fs-5 fw-bold text-primary">₹${item.price}</span>
                            <div>
                                <button class="btn btn-sm btn-outline-danger me-2 btn-remove-wishlist" data-id="${item.id}" title="Remove from Wishlist">
                                    <i class="bi bi-trash"></i>
                                </button>
                                <button class="btn btn-sm btn-primary rounded-pill px-3 btn-add-wishlist-cart" 
                                    data-id="${item.id}" 
                                    data-title="${item.title}" 
                                    data-price="${item.price}" 
                                    data-img="${item.img}" 
                                    data-author="${item.author}">
                                    Add to Cart
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;

    // Bind Wishlist buttons
    document.querySelectorAll('.btn-remove-wishlist').forEach(btn => {
        btn.addEventListener('click', () => {
            removeFromWishlist(btn.dataset.id);
            renderWishlistPage();
        });
    });

    document.querySelectorAll('.btn-add-wishlist-cart').forEach(btn => {
        btn.addEventListener('click', () => {
            const book = {
                id: btn.dataset.id,
                title: btn.dataset.title,
                price: btn.dataset.price,
                img: btn.dataset.img,
                author: btn.dataset.author
            };
            addToCart(book);
        });
    });
}

function renderCheckoutPage() {
    const itemsContainer = document.getElementById('checkout-items-list');
    const subtotalEl = document.getElementById('checkout-subtotal');
    const totalEl = document.getElementById('checkout-total');
    const submitBtn = document.getElementById('place-order-btn');

    if (!itemsContainer) return;

    const cart = getCart();

    if (cart.length === 0) {
        itemsContainer.innerHTML = `<div class="text-danger fw-bold py-2">Your cart is empty. Cannot checkout.</div>`;
        if (submitBtn) submitBtn.disabled = true;
        return;
    }

    let html = '';
    let total = 0;

    cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        html += `
            <div class="d-flex justify-content-between mb-2">
                <span>${item.title} <span class="text-muted">x${item.quantity}</span></span>
                <strong>₹${itemTotal}</strong>
            </div>
        `;
    });

    itemsContainer.innerHTML = html;
    if (subtotalEl) subtotalEl.textContent = `₹${total}`;
    if (totalEl) totalEl.textContent = `₹${total}`;

    // Store total in localStorage temporarily on form submit to display it in orders.html
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', () => {
            localStorage.setItem('bookbazar_last_order_total', total);
            const selectedPayment = document.querySelector('input[name="payment"]:checked')?.value || 'COD';
            let paymentText = 'Cash on Delivery';
            if (selectedPayment === 'UPI') paymentText = 'UPI';
            if (selectedPayment === 'CARD') paymentText = 'Credit / Debit Card';
            localStorage.setItem('bookbazar_last_payment_method', paymentText);

            const randomOrderId = '#ORD-' + Math.floor(1000 + Math.random() * 9000);
            localStorage.setItem('bookbazar_last_order_id', randomOrderId);

            localStorage.removeItem('bookbazar_cart');
        });
    }
}

function renderOrderConfirmedPage() {
    const orderIdEl = document.getElementById('confirmed-order-id');
    const paymentMethodEl = document.getElementById('confirmed-payment-method');
    const totalAmountEl = document.getElementById('confirmed-total-amount');

    if (!orderIdEl && !paymentMethodEl && !totalAmountEl) return;

    const lastTotal = localStorage.getItem('bookbazar_last_order_total');
    const lastPayment = localStorage.getItem('bookbazar_last_payment_method');
    const lastOrderId = localStorage.getItem('bookbazar_last_order_id');

    if (lastOrderId) {
        if (orderIdEl) orderIdEl.textContent = lastOrderId;
        if (paymentMethodEl) paymentMethodEl.textContent = lastPayment || 'Cash on Delivery';
        if (totalAmountEl) totalAmountEl.textContent = `₹${lastTotal || '0.00'}`;
        
        localStorage.removeItem('bookbazar_last_order_total');
        localStorage.removeItem('bookbazar_last_payment_method');
        localStorage.removeItem('bookbazar_last_order_id');
    }
}

window.currentCategoryFilter = 'all';

function renderBooksPage() {
    const container = document.getElementById('books-grid');
    if (!container) return;

    const catalog = getCatalog();
    const activeFilterBtn = document.querySelector('.filter-btn.active');
    const filter = activeFilterBtn ? activeFilterBtn.getAttribute('data-filter') : 'all';
    const categoryFilter = window.currentCategoryFilter || 'all';

    let html = '';
    catalog.forEach(item => {
        // Skip unapproved books in public shop
        if (item.approved === false) {
            return;
        }

        // Filter by condition
        if (filter !== 'all' && item.condition !== filter) {
            return;
        }

        // Filter by category
        if (categoryFilter !== 'all' && item.category !== categoryFilter) {
            return;
        }

        const isNew = item.condition === 'new';
        const badgeClass = isNew ? 'bg-success' : 'bg-purple';
        const badgeStyle = isNew ? '' : 'style="background-color: #a855f7;"';
        const badgeText = isNew ? 'New' : 'Pre-Loved';

        html += `
            <div class="col-md-3 book-item-col" data-condition="${item.condition}">
                <div class="card h-100 border-0 shadow-sm rounded-4 overflow-hidden position-relative" style="${isNew ? '' : 'background: #111114;'}">
                    <span class="position-absolute top-0 start-0 m-3 badge ${badgeClass} text-white px-3 py-2 rounded-pill" ${badgeStyle}>${badgeText}</span>
                    <img src="${item.img || 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=300'}" class="card-img-top" alt="${item.title}" style="height: 300px; object-fit: cover;">
                    <div class="card-body p-4 d-flex flex-column">
                        <h5 class="fw-bold mb-1 text-white">${item.title}</h5>
                        <p class="text-muted small mb-3">${item.author}</p>
                        <div class="d-flex justify-content-between align-items-center mt-auto">
                            <span class="fs-5 fw-bold text-primary">₹${item.price}</span>
                            <a href="/book/${item.id}" class="btn btn-sm btn-primary rounded-pill px-3">View Details</a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function resizeAndConvertImage(file, callback) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            const canvas = document.createElement('canvas');
            const max_width = 300;
            const max_height = 400;
            let width = img.width;
            let height = img.height;

            if (width > height) {
                if (width > max_width) {
                    height *= max_width / width;
                    width = max_width;
                }
            } else {
                if (height > max_height) {
                    width *= max_height / height;
                    height = max_height;
                }
            }

            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
            callback(dataUrl);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function setupSellBookForm() {
    const form = document.getElementById('sell-book-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        if (window.isUserLoggedIn === false) {
            window.location.href = '/login';
            return;
        }

        const title = document.getElementById('sell-title').value;
        const author = document.getElementById('sell-author').value;
        const category = document.getElementById('sell-category').value;
        const price = document.getElementById('sell-price').value;
        const conditionText = document.getElementById('sell-condition').value;
        const notes = document.getElementById('sell-notes').value;

        const fileInput = document.getElementById('sell-img-file');
        const file = fileInput ? fileInput.files[0] : null;
        const submitBook = (imgData) => {
            const newBook = {
                id: Date.now(),
                title: title,
                author: author,
                price: Number(price),
                img: imgData,
                condition: 'pre-loved',
                category: category,
                description: `Condition: ${conditionText}. ${notes}`
            };

            addBookToCatalog(newBook);
            showNotification(`"${title}" listed successfully!`, 'success');

            setTimeout(() => {
                window.location.href = '/books';
            }, 1000);
        };

        if (file) {
            resizeAndConvertImage(file, (imgData) => {
                submitBook(imgData);
            });
        } else {
            submitBook('https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=300');
        }
    });
}

function loadUserBookDetails() {
    const container = document.getElementById('dynamic-book-details-anchor');
    if (!container) return;

    const bookId = window.currentBookId;
    if (!bookId) return;

    const catalog = getCatalog();
    const book = catalog.find(item => item.id == bookId);
    if (!book) return;

    const titleEl = document.getElementById('detail-title');
    const authorEl = document.getElementById('detail-author');
    const priceEl = document.getElementById('detail-price');
    const imgEl = document.getElementById('detail-image');
    const descEl = document.getElementById('detail-description');
    const condEl = document.getElementById('detail-condition');

    if (titleEl) titleEl.textContent = book.title;
    if (authorEl) authorEl.textContent = book.author;
    if (priceEl) priceEl.textContent = `₹${book.price}`;
    if (imgEl) {
        imgEl.src = book.img;
        imgEl.alt = book.title;
    }
    if (descEl) descEl.textContent = book.description;
    if (condEl) condEl.textContent = book.condition === 'new' ? 'New' : 'Pre-Loved';

    document.querySelectorAll('.add-to-cart-btn, .add-to-wishlist-btn').forEach(btn => {
        btn.dataset.id = book.id;
        btn.dataset.title = book.title;
        btn.dataset.price = book.price;
        btn.dataset.img = book.img;
        btn.dataset.author = book.author;
    });
}

function renderAdminBooksPage() {
    const activeTable = document.getElementById('admin-active-books-table-body');
    const pendingTable = document.getElementById('admin-pending-books-table-body');
    
    if (!activeTable && !pendingTable) return;

    const catalog = getCatalog();
    // Sort catalog by ID descending (newest uploaded first)
    const sortedCatalog = [...catalog].sort((a, b) => b.id - a.id);

    let activeHtml = '';
    let pendingHtml = '';

    let activeCount = 0;
    const showAll = window.showAllAdminBooks === true;

    // Count total active (approved) books in the catalog
    const totalActiveBooks = sortedCatalog.filter(item => item.approved !== false).length;

    sortedCatalog.forEach(item => {
        const isApproved = item.approved !== false;
        const isNew = item.condition === 'new';
        const typeBadge = isNew ? 'New' : 'Pre-Loved';

        if (isApproved) {
            // If not showAll, only display up to 5
            if (!showAll && activeCount >= 5) {
                return;
            }
            activeCount++;
            activeHtml += `
                <tr>
                    <td><img src="${item.img}" alt="${item.title}" class="rounded" style="width: 50px; height: 70px; object-fit: cover;"></td>
                    <td><strong class="text-white">${item.title}</strong></td>
                    <td class="text-white">${item.author}</td>
                    <td class="text-white">${item.seller_name || 'Store'}</td>
                    <td class="text-white">₹${item.price}</td>
                    <td class="text-white">${typeBadge}</td>
                    <td><span class="badge bg-success bg-opacity-10 text-success px-3 py-2 rounded-pill">Active</span></td>
                    <td>
                        <a href="/admin/edit-book/${item.id}" class="btn btn-sm btn-outline-secondary me-2"><i class="bi bi-pencil"></i></a>
                        <button class="btn btn-sm btn-outline-danger btn-delete-admin-book" data-id="${item.id}"><i class="bi bi-trash"></i></button>
                    </td>
                </tr>
            `;
        } else {
            pendingHtml += `
                <tr class="table-warning bg-opacity-10">
                    <td><img src="${item.img}" alt="${item.title}" class="rounded" style="width: 50px; height: 70px; object-fit: cover;"></td>
                    <td><strong class="text-white">${item.title}</strong></td>
                    <td class="text-white">${item.author}</td>
                    <td class="text-white">${item.seller_name || 'Store'}</td>
                    <td class="text-white">₹${item.price}</td>
                    <td class="text-white">${typeBadge}</td>
                    <td><span class="badge bg-warning bg-opacity-10 text-warning px-3 py-2 rounded-pill">Pending Approval</span></td>
                    <td>
                        <button class="btn btn-sm btn-success me-2 btn-approve-admin-book" data-id="${item.id}"><i class="bi bi-check-lg"></i> Approve</button>
                        <a href="/admin/edit-book/${item.id}" class="btn btn-sm btn-outline-secondary me-2"><i class="bi bi-pencil"></i></a>
                        <button class="btn btn-sm btn-outline-danger btn-delete-admin-book" data-id="${item.id}"><i class="bi bi-trash"></i> Reject</button>
                    </td>
                </tr>
            `;
        }
    });

    if (activeTable) {
        activeTable.innerHTML = activeHtml || '<tr><td colspan="8" class="text-center text-muted py-4">No active books in catalog.</td></tr>';
    }
    
    if (pendingTable) {
        pendingTable.innerHTML = pendingHtml || '<tr><td colspan="8" class="text-center text-muted py-4">No pending book submissions.</td></tr>';
    }

    // Toggle button visibility and text
    const viewAllContainer = document.getElementById('view-all-books-container');
    if (viewAllContainer) {
        if (totalActiveBooks > 5) {
            viewAllContainer.style.display = 'block';
            const btn = document.getElementById('btn-view-all-books');
            if (btn) {
                btn.innerHTML = showAll 
                    ? '<i class="bi bi-eye-slash"></i> Show Less' 
                    : `<i class="bi bi-eye"></i> View All Books (${totalActiveBooks})`;
            }
        } else {
            viewAllContainer.style.display = 'none';
        }
    }

    // Bind action listeners
    document.querySelectorAll('.btn-approve-admin-book').forEach(btn => {
        btn.addEventListener('click', () => {
            approveBook(btn.dataset.id);
        });
    });

    document.querySelectorAll('.btn-delete-admin-book').forEach(btn => {
        btn.addEventListener('click', () => {
            if (confirm('Are you sure you want to remove/reject this book?')) {
                deleteBook(btn.dataset.id);
            }
        });
    });
}

function approveBook(id) {
    const catalog = getCatalog();
    const book = catalog.find(item => item.id == id);
    if (book) {
        book.approved = true;
        saveCatalog(catalog);
        showNotification(`"${book.title}" approved and live in shop!`, 'success');
        renderAdminBooksPage();
        
        // Sync to server
        fetch('/api/admin/book/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ book_id: id })
        });
    }
}

function deleteBook(id) {
    let catalog = getCatalog();
    const book = catalog.find(item => item.id == id);
    if (book) {
        catalog = catalog.filter(item => item.id != id);
        saveCatalog(catalog);
        showNotification(`Listing for "${book.title}" removed.`, 'danger');
        renderAdminBooksPage();
        
        // Sync to server
        fetch('/api/admin/book/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ book_id: id })
        });
    }
}

function renderUserSubmissions() {
    const tableBody = document.getElementById('user-submissions-table-body');
    if (!tableBody) return;

    const catalog = getCatalog();
    const currentUserId = window.currentUserId;
    const userBooks = catalog.filter(item => item.seller_id && currentUserId && item.seller_id == currentUserId);

    let html = '';
    userBooks.forEach(item => {
        const isApproved = item.approved !== false;
        const statusBadge = isApproved 
            ? '<span class="badge bg-success bg-opacity-10 text-success px-3 py-2 rounded-pill"><i class="bi bi-check-circle-fill me-1"></i>Approved & Live</span>'
            : '<span class="badge bg-warning bg-opacity-10 text-warning px-3 py-2 rounded-pill"><i class="bi bi-hourglass-split me-1"></i>Pending Approval</span>';

        html += `
            <tr>
                <td><img src="${item.img}" alt="${item.title}" class="rounded" style="width: 40px; height: 55px; object-fit: cover;"></td>
                <td><strong class="text-white">${item.title}</strong></td>
                <td class="text-white">${item.author}</td>
                <td class="text-white">₹${item.price}</td>
                <td>${statusBadge}</td>
            </tr>
        `;
    });

    tableBody.innerHTML = html || '<tr><td colspan="5" class="text-center text-muted py-4">You haven\'t listed any books for sale yet.</td></tr>';
}

// 5. Global click delegate for "Add to Cart" and "Add to Wishlist" buttons
document.addEventListener('DOMContentLoaded', () => {
    // Sync data from database on page load
    fetch('/api/sync_data')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                console.error("Failed to sync database data:", data.error);
                return;
            }
            
            window.currentUserId = data.user_id;
            
            // Seed localStorage from database
            localStorage.setItem('bookbazar_catalog', JSON.stringify(data.catalog));
            if (data.isLoggedIn) {
                localStorage.setItem('bookbazar_cart', JSON.stringify(data.cart));
                localStorage.setItem('bookbazar_wishlist', JSON.stringify(data.wishlist));
            } else {
                localStorage.removeItem('bookbazar_cart');
                localStorage.removeItem('bookbazar_wishlist');
                localStorage.removeItem('bookbazar_last_order_total');
                localStorage.removeItem('bookbazar_last_payment_method');
                localStorage.removeItem('bookbazar_last_order_id');
            }

            // Initial UI state setup
            updateBadges();

            // Specific page renderers
            renderCartPage();
            renderWishlistPage();
            renderCheckoutPage();
            renderOrderConfirmedPage();

            // Extract category query parameter first
            const urlParams = new URLSearchParams(window.location.search);
            const catParam = urlParams.get('category');
            if (catParam) {
                window.currentCategoryFilter = catParam;
                
                // Highlight the matching item in the dropdown
                document.querySelectorAll('.category-filter-item').forEach(el => {
                    if (el.getAttribute('data-category') === catParam) {
                        el.classList.add('active');
                    } else {
                        el.classList.remove('active');
                    }
                });

                const label = document.getElementById('current-category');
                if (label) {
                    label.textContent = catParam;
                }
            }

            renderBooksPage();
            setupSellBookForm();
            loadUserBookDetails();
            renderAdminBooksPage();
            renderUserSubmissions();

            // Bind View All Books button in admin panel
            const viewAllBtn = document.getElementById('btn-view-all-books');
            if (viewAllBtn) {
                viewAllBtn.addEventListener('click', () => {
                    window.showAllAdminBooks = !window.showAllAdminBooks;
                    renderAdminBooksPage();
                });
            }

            // Bind Category Filter dropdown items
            document.querySelectorAll('.category-filter-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    document.querySelectorAll('.category-filter-item').forEach(el => el.classList.remove('active'));
                    item.classList.add('active');
                    window.currentCategoryFilter = item.getAttribute('data-category');
                    
                    // Update dropdown label text
                    const label = document.getElementById('current-category');
                    if (label) {
                        label.textContent = window.currentCategoryFilter === 'all' ? 'All' : window.currentCategoryFilter;
                    }

                    renderBooksPage();
                });
            });

            // Bind Filter buttons
            document.querySelectorAll('.filter-btn').forEach(button => {
                button.addEventListener('click', () => {
                    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
                    button.classList.add('active');
                    renderBooksPage();
                });
            });

            // Event Delegation
            document.addEventListener('click', (e) => {
                // Add to Cart
                const addToCartBtn = e.target.closest('.add-to-cart-btn');
                if (addToCartBtn) {
                    e.preventDefault();
                    const book = {
                        id: addToCartBtn.dataset.id,
                        title: addToCartBtn.dataset.title,
                        price: addToCartBtn.dataset.price,
                        img: addToCartBtn.dataset.img,
                        author: addToCartBtn.dataset.author
                    };
                    addToCart(book);
                }

                // Add to Wishlist
                const addToWishlistBtn = e.target.closest('.add-to-wishlist-btn');
                if (addToWishlistBtn) {
                    e.preventDefault();
                    const book = {
                        id: addToWishlistBtn.dataset.id,
                        title: addToWishlistBtn.dataset.title,
                        price: addToWishlistBtn.dataset.price,
                        img: addToWishlistBtn.dataset.img,
                        author: addToWishlistBtn.dataset.author
                    };
                    addToWishlist(book);

                    if (addToWishlistBtn.classList.contains('btn-outline-secondary')) {
                        addToWishlistBtn.classList.remove('btn-outline-secondary');
                        addToWishlistBtn.classList.add('btn-danger', 'text-white');
                    }
                }
            });

            // Cross-tab real-time catalog approval synchronization
            window.addEventListener('storage', (e) => {
                if (e.key === 'bookbazar_catalog') {
                    renderBooksPage();
                    renderAdminBooksPage();
                    renderUserSubmissions();
                }
            });
        });
});
