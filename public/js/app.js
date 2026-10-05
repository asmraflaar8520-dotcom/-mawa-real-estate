// MA'WA Core Frontend Application Logic
const API_BASE = '/api';

const App = {
  token: localStorage.getItem('mawa_token') || null,
  user: JSON.parse(localStorage.getItem('mawa_user') || 'null'),
  compareList: JSON.parse(localStorage.getItem('mawa_compare') || '[]'),

  init() {
    this.updateAuthUI();
    this.updateCompareBadge();
  },

  setAuth(token, user) {
    this.token = token;
    this.user = user;
    localStorage.setItem('mawa_token', token);
    localStorage.setItem('mawa_user', JSON.stringify(user));
    this.updateAuthUI();
  },

  async logout() {
    if (this.token) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: this.getAuthHeaders()
        });
      } catch (e) {
        // Continue clearing client credentials even if network fails
      }
    }
    this.token = null;
    this.user = null;
    localStorage.removeItem('mawa_token');
    localStorage.removeItem('mawa_user');
    this.updateAuthUI();
    this.showToast('تم تسجيل الخروج بنجاح');
    if (window.location.pathname.includes('dashboard.html')) {
      window.location.href = '/login.html';
    }
  },

  getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  },

  escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  },

  sanitizeUrl(url) {
    if (!url) return '';
    const clean = String(url).trim();
    if (clean.startsWith('/') || clean.startsWith('https://') || clean.startsWith('http://')) {
      return clean.replace(/[<>"']/g, encodeURIComponent);
    }
    return '';
  },

  updateAuthUI() {
    const authActions = document.getElementById('nav-auth-actions');
    if (!authActions) return;

    if (this.user) {
      const safeName = this.escapeHtml(this.user.full_name || 'المستخدم');
      authActions.innerHTML = `
        <span class="user-greeting" style="font-size:0.85rem; font-weight:700; color:var(--color-primary);">
          مرحباً، ${safeName}
        </span>
        <a href="/dashboard.html" class="btn btn-secondary btn-sm">لوحة التحكم</a>
        <button onclick="App.logout()" class="btn btn-outline btn-sm">خروج</button>
      `;
    } else {
      authActions.innerHTML = `
        <a href="/login.html" class="btn btn-outline btn-sm">تسجيل الدخول</a>
        <a href="/register.html" class="btn btn-primary btn-sm">حساب جديد</a>
      `;
    }
  },

  showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.backgroundColor = type === 'error' ? 'var(--color-error)' : '#0b2545';
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 4000);
  },

  // Comparison Management
  toggleCompare(propId) {
    const index = this.compareList.indexOf(propId);
    if (index > -1) {
      this.compareList.splice(index, 1);
      this.showToast('تمت إزالة العقار من قائمة المقارنة');
    } else {
      if (this.compareList.length >= 4) {
        this.showToast('يمكنك مقارنة ما يصل إلى 4 عقارات فقط كحد أقصى', 'error');
        return;
      }
      this.compareList.push(propId);
      this.showToast('تمت إضافة العقار للمقارنة المحايدة');
    }
    localStorage.setItem('mawa_compare', JSON.stringify(this.compareList));
    this.updateCompareBadge();
  },

  updateCompareBadge() {
    const badge = document.getElementById('compare-count-badge');
    if (badge) {
      badge.textContent = this.compareList.length;
      badge.style.display = this.compareList.length > 0 ? 'inline-flex' : 'none';
    }
    const mobileBadge = document.getElementById('mobile-compare-badge');
    if (mobileBadge) {
      mobileBadge.textContent = this.compareList.length;
      mobileBadge.style.display = this.compareList.length > 0 ? 'flex' : 'none';
    }
  },

  goToCompare() {
    if (this.compareList.length < 2) {
      this.showToast('يرجى اختيار عقارين على الأقل لبدء المقارنة الفنية المحايدة', 'error');
      return;
    }
    window.location.href = `/compare.html?ids=${this.compareList.join(',')}`;
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
