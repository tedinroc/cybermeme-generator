class I18n {
    constructor() {
        this.translations = {};
        this.supportedLocales = ['en-US', 'zh-TW'];
        // 先從 localStorage 讀取，如果沒有再使用瀏覽器語言
        this.currentLocale = localStorage.getItem('preferredLocale') || this.getBrowserLocale() || 'en-US';
    }

    getBrowserLocale() {
        const browserLang = navigator.language;
        // 檢查完整匹配
        if (this.supportedLocales.includes(browserLang)) {
            return browserLang;
        }
        // 檢查語言代碼匹配（例如 'zh' 匹配 'zh-TW'）
        const langCode = browserLang.split('-')[0];
        const match = this.supportedLocales.find(locale => locale.startsWith(langCode));
        return match || 'en-US';
    }

    async init() {
        try {
            // 載入所有支援的語言檔
            const loadPromises = this.supportedLocales.map(async locale => {
                try {
                    const response = await fetch(`/static/locales/${locale}.json`);
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    this.translations[locale] = await response.json();
                } catch (error) {
                    console.error(`Failed to load translations for ${locale}:`, error);
                    // 如果載入失敗，使用空對象防止錯誤
                    this.translations[locale] = {};
                }
            });

            await Promise.all(loadPromises);
            console.log('Translations loaded:', Object.keys(this.translations));

            // 創建語言選擇器
            this.createLanguageSelector();
            
            // 初始翻譯
            this.translate();
            
            // 添加 debug 信息
            console.log('Current locale:', this.currentLocale);
            console.log('Available translations:', this.translations);
        } catch (error) {
            console.error('初始化失敗:', error);
        }
    }

    createLanguageSelector() {
        // 移除現有的選擇器（如果存在）
        const existingSelector = document.querySelector('.language-selector-container');
        if (existingSelector) {
            existingSelector.remove();
        }

        // 創建新的選擇器容器
        const container = document.createElement('div');
        container.className = 'language-selector-container';

        // 創建選擇器
        const selector = document.createElement('select');
        selector.className = 'cyberpunk-select';

        // 添加語言選項
        this.supportedLocales.forEach(locale => {
            const option = document.createElement('option');
            option.value = locale;
            option.textContent = locale === 'en-US' ? 'English' : '繁體中文';
            option.selected = locale === this.currentLocale;
            selector.appendChild(option);
        });

        // 添加變更事件監聽器
        selector.addEventListener('change', (e) => {
            this.setLocale(e.target.value);
        });

        // 將選擇器添加到容器
        container.appendChild(selector);

        // 將容器添加到頁面
        document.body.insertBefore(container, document.body.firstChild);
    }

    setLocale(locale) {
        if (this.supportedLocales.includes(locale)) {
            this.currentLocale = locale;
            localStorage.setItem('preferredLocale', locale);
            this.translate();
            console.log('Language changed to:', locale);
        }
    }

    t(key) {
        try {
            const keys = key.split('.');
            let value = this.translations[this.currentLocale];
            
            for (const k of keys) {
                if (value && value[k] !== undefined) {
                    value = value[k];
                } else {
                    console.warn(`Translation missing for key: ${key} in locale: ${this.currentLocale}`);
                    // 如果當前語言找不到翻譯，嘗試使用英文
                    if (this.currentLocale !== 'en-US') {
                        return this.fallbackTranslation(key);
                    }
                    return key;
                }
            }
            
            return value;
        } catch (error) {
            console.error('Translation error:', error);
            return key;
        }
    }

    fallbackTranslation(key) {
        try {
            const keys = key.split('.');
            let value = this.translations['en-US'];
            
            for (const k of keys) {
                if (value && value[k] !== undefined) {
                    value = value[k];
                } else {
                    return key;
                }
            }
            
            return value;
        } catch (error) {
            return key;
        }
    }

    translate() {
        try {
            // 翻譯所有帶有 data-i18n 屬性的元素
            document.querySelectorAll('[data-i18n]').forEach(element => {
                const key = element.getAttribute('data-i18n');
                
                if (element.tagName === 'INPUT' && element.getAttribute('type') === 'text') {
                    element.placeholder = this.t(key);
                } else {
                    element.textContent = this.t(key);
                }
            });

            // 翻譯選項
            document.querySelectorAll('[data-i18n-options]').forEach(select => {
                const optionsKey = select.getAttribute('data-i18n-options');
                const options = this.t(optionsKey);
                
                if (typeof options === 'object') {
                    const value = select.value; // 保存當前選擇的值
                    select.innerHTML = '';
                    
                    Object.entries(options).forEach(([key, text]) => {
                        const option = document.createElement('option');
                        option.value = key;
                        option.textContent = text;
                        select.appendChild(option);
                    });
                    
                    select.value = value; // 恢復選擇的值
                }
            });

            console.log('Translation completed');
        } catch (error) {
            console.error('Translation error:', error);
        }
    }
}

// 創建全局實例
window.i18n = new I18n();

// 當 DOM 載入完成時初始化
document.addEventListener('DOMContentLoaded', () => {
    window.i18n.init();
});
