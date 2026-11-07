const initializeFrontier = () => {
  document.querySelectorAll('.remember-name').forEach((input) => {
    const savedName = localStorage.getItem('frontier-author-name');
    if (!input.value && savedName) input.value = savedName;
    input.addEventListener('input', () => localStorage.setItem('frontier-author-name', input.value));
  });

  document.querySelectorAll('[data-range-output]').forEach((input) => {
    const output = document.getElementById(input.dataset.rangeOutput);
    const update = () => { if (output) output.textContent = `${input.value}%`; };
    input.addEventListener('input', update);
    update();
  });

  document.querySelectorAll('[data-show-password]').forEach((button) => {
    button.addEventListener('click', () => {
      const input = document.getElementById(button.dataset.showPassword);
      if (!input) return;
      const showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      button.setAttribute('aria-label', showing ? 'แสดงรหัสผ่าน' : 'ซ่อนรหัสผ่าน');
      button.innerHTML = showing ? '<i class="bi bi-eye" aria-hidden="true"></i>' : '<i class="bi bi-eye-slash" aria-hidden="true"></i>';
    });
  });

  document.querySelectorAll('[data-mark-all-present]').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('input[type="radio"][value="present"]').forEach((input) => { input.checked = true; });
    });
  });

  const staffSearch = document.getElementById('staff-search-input');
  if (staffSearch) {
    const staffRows = [...document.querySelectorAll('#staff-list .staff-row')];
    const emptyRow = document.getElementById('staff-search-empty');
    const resultCount = document.getElementById('staff-search-count');

    staffSearch.addEventListener('input', () => {
      const keyword = staffSearch.value.trim().toLocaleLowerCase();
      let visibleCount = 0;

      staffRows.forEach((row) => {
        const matches = row.textContent.toLocaleLowerCase().includes(keyword);
        row.hidden = !matches;
        if (matches) visibleCount += 1;
      });

      emptyRow.hidden = visibleCount > 0;
      resultCount.textContent = keyword ? `พบ ${visibleCount} จาก ${staffRows.length} คน` : `ทั้งหมด ${staffRows.length} คน`;
    });
  }
};

document.addEventListener('click', (event) => {
  const clickedElement = event.target instanceof Element ? event.target : null;
  if (!clickedElement) return;

  const photoTrigger = clickedElement.closest('.photo-preview-trigger');
  if (photoTrigger) {
    const photoViewer = document.getElementById('photo-viewer');
    const viewerImage = photoViewer?.querySelector('.photo-viewer-image');
    if (photoViewer && viewerImage && typeof photoViewer.showModal === 'function') {
      viewerImage.src = photoTrigger.dataset.photoSrc;
      photoViewer.showModal();
    }
    return;
  }

  const photoViewer = document.getElementById('photo-viewer');
  if (clickedElement === photoViewer) photoViewer.close();

  const departmentLink = clickedElement.closest('.department-row');
  if (departmentLink) {
    const departmentDialog = document.getElementById('department-dialog');
    if (!departmentDialog || typeof departmentDialog.showModal !== 'function') return;

    event.preventDefault();
    departmentDialog.querySelector('#department-dialog-title').textContent = departmentLink.dataset.departmentName;
    departmentDialog.querySelector('.department-dialog-enter').href = departmentLink.href;
    departmentDialog.querySelector('.department-dialog-emblem i').className = departmentLink.querySelector('.department-symbol i').className;
    departmentDialog.style.setProperty('--dialog-dept', getComputedStyle(departmentLink).getPropertyValue('--dept-color'));
    departmentDialog.showModal();
    return;
  }

  if (clickedElement.matches('.department-dialog')) clickedElement.close();
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeFrontier, { once: true });
} else {
  initializeFrontier();
}