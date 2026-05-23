// Sidebar toggle with animated button
function toggleMenu() {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('menuToggle');
  const isOpen = sidebar.classList.toggle('visible');
  toggle.classList.toggle('open', isOpen);
  toggle.setAttribute('aria-label', isOpen ? 'Close menu' : 'Open menu');
}

function selectTab(sectionId) {
  showSection(sectionId);

  // update active button in sidebar
  const btns = document.querySelectorAll('.nav-btn');
  btns.forEach(b => b.classList.toggle('active', b.dataset.target === sectionId));

  if (window.innerWidth <= 768) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('menuToggle');
    sidebar.classList.remove('visible');
    toggle.classList.remove('open');
    toggle.setAttribute('aria-label', 'Open menu');
  }
}

function showSection(sectionId) {
  const sections = document.querySelectorAll('.section');
  sections.forEach(section => {
    section.classList.remove('active');
    section.classList.add('hidden');
  });

  const target = document.getElementById(sectionId);
  target.classList.remove('hidden');

  // reflow then animate
  void target.offsetWidth;
  target.classList.add('active');

  // stagger children
  const items = target.querySelectorAll('.stagger > *');
  items.forEach((el, i) => {
    el.style.animationDelay = (i * 0.06) + 's';
    el.classList.add('staggered-in');
  });
}

/* ---------------- Movement ---------------- */
function sendMove(dir) {
  fetch('/move', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'direction=' + encodeURIComponent(dir)
  });
}

/* ---------------- Volume ---------------- */
function volumeUp() {
  fetch('/volume', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'intensity=' + encodeURIComponent('increase')
  });
}
function volumeDown() {
  fetch('/volume', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'intensity=' + encodeURIComponent('decrease')
  });
}

/* ---------------- Stories ---------------- */
function playStory(name) {
  fetch('/play', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'story=' + encodeURIComponent(name)
  });
}
function stopStory(){ fetch('/story/stop', { method: 'POST' }); }
function nextStory(){ fetch('/story/next', { method: 'POST' }); }

/* ---------------- Music ---------------- */
function playMusic(name) {
  fetch('/music', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'music=' + encodeURIComponent(name)
  });
}
function stopMusic(){ fetch('/music/stop', { method: 'POST' }); }
function nextMusic(){ fetch('/music/next', { method: 'POST' }); }

/* ---------------- Education ---------------- */
function playEducation(type) {
  fetch('/education/play', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'type=' + encodeURIComponent(type)
  });
}
function stopEducation(){ fetch('/education/stop', { method: 'POST' }); }
function nextEducation(){ fetch('/education/next', { method: 'POST' }); }

/* ---------------- Camera ---------------- */
function startFeed() {
  fetch('/start', { method: 'POST' }).then(() => {
    const img = document.getElementById('stream');
    img.src = '/video_feed?ts=' + Date.now();
  });
}
function stopFeed() {
  fetch('/stop', { method: 'POST' }).then(() => {
    document.getElementById('stream').src = '';
  });
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('sidebar').classList.add('visible');
  document.getElementById('menuToggle').classList.add('open');
  const first = document.querySelector('.nav-btn[data-target="main"]');
  if (first) first.classList.add('active');
});
