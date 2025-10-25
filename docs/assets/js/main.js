// アロナちゃん - Discord服薬リマインダーBOT ドキュメントサイト用JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // ページ読み込み時のアニメーション
    const elements = document.querySelectorAll('.feature-card, .command-card, .step, .requirement-card');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease-out';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // スムーススクロール
    const navLinks = document.querySelectorAll('.nav a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // コピーボタンの追加
    const codeBlocks = document.querySelectorAll('.code-block');
    codeBlocks.forEach(block => {
        const button = document.createElement('button');
        button.innerHTML = '<i class="fas fa-copy"></i>';
        button.className = 'copy-button';
        button.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        `;
        
        block.style.position = 'relative';
        block.appendChild(button);
        
        button.addEventListener('click', function() {
            const text = block.querySelector('pre').textContent;
            navigator.clipboard.writeText(text).then(() => {
                button.innerHTML = '<i class="fas fa-check"></i>';
                button.style.background = '#28a745';
                
                setTimeout(() => {
                    button.innerHTML = '<i class="fas fa-copy"></i>';
                    button.style.background = '#667eea';
                }, 2000);
            });
        });
        
        button.addEventListener('mouseenter', function() {
            this.style.background = '#5a6fd8';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.background = '#667eea';
        });
    });

    // ダークモード切り替え（将来の拡張用）
    const darkModeToggle = document.createElement('button');
    darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    darkModeToggle.className = 'dark-mode-toggle';
    darkModeToggle.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(255,255,255,0.1);
        color: white;
        border: none;
        padding: 15px;
        border-radius: 50%;
        cursor: pointer;
        font-size: 18px;
        z-index: 1000;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    `;
    
    document.body.appendChild(darkModeToggle);
    
    darkModeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const icon = this.querySelector('i');
        if (document.body.classList.contains('dark-mode')) {
            icon.className = 'fas fa-sun';
        } else {
            icon.className = 'fas fa-moon';
        }
    });

    // 検索機能（将来の拡張用）
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'ドキュメントを検索...';
    searchInput.className = 'search-input';
    searchInput.style.cssText = `
        position: fixed;
        top: 20px;
        left: 20px;
        padding: 10px 15px;
        border: none;
        border-radius: 25px;
        background: rgba(255,255,255,0.1);
        color: white;
        backdrop-filter: blur(10px);
        z-index: 1000;
        width: 250px;
        transition: all 0.3s ease;
    `;
    
    document.body.appendChild(searchInput);
    
    searchInput.addEventListener('focus', function() {
        this.style.width = '300px';
        this.style.background = 'rgba(255,255,255,0.2)';
    });
    
    searchInput.addEventListener('blur', function() {
        this.style.width = '250px';
        this.style.background = 'rgba(255,255,255,0.1)';
    });

    // ツールチップの追加
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: absolute;
                background: #333;
                color: white;
                padding: 8px 12px;
                border-radius: 5px;
                font-size: 14px;
                z-index: 1000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + 'px';
            tooltip.style.top = (rect.top - 40) + 'px';
            
            setTimeout(() => {
                tooltip.style.opacity = '1';
            }, 10);
            
            this.tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this.tooltip) {
                this.tooltip.remove();
                this.tooltip = null;
            }
        });
    });

    // ページ内リンクのハイライト
    const currentPage = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('.nav a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        }
    });

    // スクロール時のヘッダー効果
    let lastScrollTop = 0;
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const header = document.querySelector('.header');
        
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            // 下にスクロール
            header.style.transform = 'translateY(-100%)';
        } else {
            // 上にスクロール
            header.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = scrollTop;
    });

    // キーボードショートカット
    document.addEventListener('keydown', function(e) {
        // Ctrl + K で検索フォーカス
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }
        
        // Escape で検索クリア
        if (e.key === 'Escape') {
            searchInput.blur();
            searchInput.value = '';
        }
    });

    // パフォーマンス最適化
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    const animatedElements = document.querySelectorAll('.feature-card, .command-card, .step');
    animatedElements.forEach(el => observer.observe(el));

    // コンソールメッセージ
    console.log(`
    💊 アロナちゃん - Discord服薬リマインダーBOT
    
    🎯 利用可能なショートカット:
    - Ctrl + K: 検索フォーカス
    - Escape: 検索クリア
    
    📚 ドキュメント:
    - ホーム: index.html
    - 機能詳細: features.html
    - セットアップ: setup.html
    - コマンド: commands.html
    
    🚀 GitHub Pages: https://[ユーザー名].github.io/[リポジトリ名]
    `);
});
