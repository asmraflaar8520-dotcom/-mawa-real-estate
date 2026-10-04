// MA'WA Check — قائمة التدقيق الفني والإرشادي الذكي للمشتري
const MawaCheck = {
  questions: [
    { id: 'c1', label: 'وضوح السعر الإجمالي وسعر المتر المحسوب بدقة', desc: 'تم تدقيق السعر المعلن ومقارنته بمتوسط الأسعار بالمنطقة' },
    { id: 'c2', label: 'المساحة الصافية والحصة في الأرض', desc: 'تم توضيح نسبة الخدمات والحصة المشاعة بالعقد المسجل' },
    { id: 'c3', label: 'توثيق هوية الوسيط والاعتماد المهني', desc: 'تم التحقق من مطابقة بطاقة الرقم القومي ورخصة الوساطة العقارية' },
    { id: 'c4', label: 'موقف رخصة البناء ومحاضر الحي', desc: 'تم التحقق من صدور رخصة البناء الرسمية وعدم وجود مخالفات هدم أو إزالة' },
    { id: 'c5', label: 'عدادات المرافق الأساسية (كهرباء، مياه، غاز)', desc: 'التأكد من تركيب العدادات القانونية وبراءة ذمة المالك من الفواتير القديمة' },
    { id: 'c6', label: 'وديعة الصيانة ومصروفات الحراسة والمصعد', desc: 'تحديد قيمة وديعة الصيانة المودعة بالبنك والتزامات إدارة العقار' },
    { id: 'c7', label: 'التفاوض وشروط السداد', desc: 'تحديد ما إذا كان السعر نهائياً كاش أو متاحاً للتقسيط والتفاوض بالتراضي' }
  ],

  openModal(propertyData) {
    let modal = document.getElementById('mawa-check-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'mawa-check-modal';
      modal.className = 'modal-overlay';
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');
      modal.setAttribute('aria-labelledby', 'mawa-check-modal-title');
      document.body.appendChild(modal);

      // Keyboard accessibility: Close on Escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
          MawaCheck.closeModal();
        }
      });
    }

    const safePropId = propertyData ? App.escapeHtml(propertyData.id) : '';

    const itemsHtml = this.questions.map((q, idx) => `
      <div class="checklist-item" style="display:flex; gap:0.75rem; align-items:flex-start; margin-bottom:0.75rem;">
        <input type="checkbox" id="check_${q.id}" style="width:20px; height:20px; accent-color:var(--color-primary); cursor:pointer; margin-top:2px;">
        <label for="check_${q.id}" style="cursor:pointer;">
          <div style="font-weight:700; font-size:0.92rem; color:var(--color-on-surface);">${idx + 1}. ${q.label}</div>
          <div style="font-size:0.8rem; color:var(--color-on-surface-variant); margin-top:2px;">${q.desc}</div>
        </label>
      </div>
    `).join('');

    modal.innerHTML = `
      <div class="modal-card">
        <div class="modal-header">
          <div>
            <h3 id="mawa-check-modal-title" style="color:var(--color-primary); display:flex; align-items:center; gap:0.5rem;">
              <span>🛡️ فحص مأوى الذكي</span>
              <span style="font-size:0.75rem; background:#e0ecfb; color:var(--color-primary); padding:2px 8px; border-radius:var(--radius-full);">إرشادي وتوعوي</span>
            </h3>
            <p style="font-size:0.8rem; color:var(--color-on-surface-variant); margin-top:4px;">
              قائمة التحقق الموصى بها قبل طلب المعاينة أو إتمام أي تعاقد عقاري بمحافظة الغربية.
            </p>
          </div>
          <button class="modal-close" onclick="MawaCheck.closeModal()" aria-label="إغلاق النافذة">&times;</button>
        </div>

        <div style="margin-bottom:1rem; padding:0.75rem; background:#fef9ee; border-radius:var(--radius-md); border:1px solid #f6d289; font-size:0.82rem; color:#855502;">
          <strong>تنويه قانوني هام:</strong> "فحص مأوى" هو دليل إرشادي لتنظيم عملية الشراء ولا يُعد شهادة ملكية رسمية أو استشارة قانونية تغني عن فحص العقود بالشهر العقاري.
        </div>

        <div class="checklist-group">
          ${itemsHtml}
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--color-outline-variant); padding-top:1rem; margin-top:1rem;">
          <span id="check-counter" style="font-size:0.85rem; font-weight:700; color:var(--color-secondary);">
            تم إكمال 0 من ${this.questions.length} عناصر
          </span>
          <button onclick="MawaCheck.confirmAndProceed('${safePropId}')" class="btn btn-primary btn-sm">
            متابعة المعاينة بالتراضي
          </button>
        </div>
      </div>
    `;

    modal.classList.add('active');

    // Attach listeners to update counter
    modal.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.addEventListener('change', () => {
        const checkedCount = modal.querySelectorAll('input[type="checkbox"]:checked').length;
        document.getElementById('check-counter').textContent = `تم إكمال ${checkedCount} من ${this.questions.length} عناصر`;
      });
    });
  },

  closeModal() {
    const modal = document.getElementById('mawa-check-modal');
    if (modal) modal.classList.remove('active');
  },

  confirmAndProceed(propId) {
    this.closeModal();
    if (propId && window.openViewingModal) {
      window.openViewingModal(propId);
    }
  }
};
