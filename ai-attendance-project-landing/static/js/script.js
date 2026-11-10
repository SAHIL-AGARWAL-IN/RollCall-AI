// Motion for the landing page. Every animated element already shows its final state in the HTML;
// this only rewinds and replays it, and does nothing for people who ask for reduced motion.
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// The hero phone takes one class after another: scan the photo, mark the register, save.
// kids: one per seat in the photo. m = matched, w = weak match, u = nobody matched, - = empty seat.
// rows: [name, where they were seen (null = absent), worth a check?]
const CLASSES = [
    {
        code: 'CS101', subject: 'Introduction to Computer Science',
        kids: ['m', 'm', 'u', 'm', 'm', '-', 'm', 'm'],
        rows: [['Aarav Sharma', 'photo 1'], ['Ananya Iyer', 'photo 1'], ['Dev Patel', null],
            ['Diya Kapoor', 'photo 1'], ['Hamza Rizvi', 'photo 1'], ['Kavya Nair', 'photo 1'],
            ['Rohan Gupta', null], ['Zoya Siddiqui', 'photo 1']],
        flag: "1 face didn't match any student",
    },
    {
        code: 'MA102', subject: 'Discrete Mathematics',
        kids: ['m', 'w', 'm', 'm', 'm', 'm', '-', 'm'],
        rows: [['Aditi Rao', 'photo 1'], ['Arjun Mehta', 'photo 1'], ['Bhavya Shah', 'photo 1'],
            ['Esha Chatterjee', 'photo 1', true], ['Farhan Ali', 'photo 1'], ['Isha Saxena', null],
            ['Kabir Malhotra', 'photo 1'], ['Meera Pillai', 'photo 1']],
        flag: 'Weak match for Esha Chatterjee. Check before saving.',
    },
    {
        code: 'PH110', subject: 'Engineering Physics',
        kids: ['m', '-', 'm', 'm', 'm', 'm', 'm', '-'],
        rows: [['Neel Banerjee', 'photo 1'], ['Priya Menon', 'photo 1'], ['Rahul Desai', 'photo 1'],
            ['Riya Sen', null], ['Sara Khan', 'photo 1'], ['Tanvi Kulkarni', 'photo 1'],
            ['Vihaan Joshi', null], ['Zoya Siddiqui', 'photo 1']],
        flag: null,
    },
];

class Stopped extends Error {}

function heroPhone() {
    const phone = document.querySelector('[data-phone]');
    const toggle = document.querySelector('[data-loop-toggle]');
    if (!phone || reduceMotion) return;

    const $ = (sel) => phone.querySelector(sel);
    const kids = [...phone.querySelectorAll('.kid')];
    const register = $('[data-register]');
    const tally = $('[data-tally]');
    let run = null;          // the loop currently playing, if any
    let next = 0;            // which class plays next
    let onScreen = false;
    let paused = false;

    const wait = (ms, current) => new Promise((resolve, reject) => {
        setTimeout(() => (current.stopped ? reject(new Stopped()) : resolve()), ms);
    });

    // Each view is relabelled only while it's hidden, so a header never changes on screen
    function showClass(view, c) {
        phone.querySelector(`${view} [data-code]`).textContent = c.code;
        phone.querySelector(`${view} [data-subject]`).textContent = c.subject;
    }

    async function scan(c, current) {
        showClass('.view-scan', c);
        phone.dataset.phase = 'scan';
        $('[data-status]').textContent = 'Looking for faces…';
        kids.forEach((kid, i) => {
            kid.classList.remove('found', 'weak', 'unknown', 'empty');
            if (c.kids[i] === '-') kid.classList.add('empty');
        });

        const line = $('[data-scan-line]');
        line.classList.remove('sweeping');
        void line.offsetWidth;   // restart the sweep
        await wait(350, current);
        line.classList.add('sweeping');

        // Boxes land on faces as the sweep passes them: back row first, then the front
        let faces = 0;
        for (const i of [0, 1, 2, 3, 4, 5, 6, 7]) {
            if (c.kids[i] === '-') continue;
            await wait(150, current);
            kids[i].classList.add('found');
            if (c.kids[i] === 'w') kids[i].classList.add('weak');
            if (c.kids[i] === 'u') kids[i].classList.add('unknown');
            faces += 1;
        }
        $('[data-status]').textContent = `Found ${faces} faces`;
        await wait(1000, current);
    }

    async function mark(c, current) {
        register.replaceChildren(...c.rows.map(([name, seen, check]) => {
            const li = document.createElement('li');
            li.className = seen ? 'present' : 'absent';
            const box = document.createElement('span');
            box.className = 'box';
            const note = document.createElement('em');
            note.textContent = seen ? (check ? `${seen}, weak match` : seen) : 'absent';
            if (check) note.className = 'weak';
            li.append(box, name, note);
            return li;
        }));
        register.classList.add('is-marking');
        showClass('.view-register', c);
        tally.textContent = '0';
        $('[data-of]').textContent = `of ${c.rows.length} present`;
        const flag = $('[data-flag]');
        flag.classList.remove('shown');
        flag.classList.toggle('calm', !c.flag);
        flag.textContent = c.flag || 'Nothing looks off';
        $('[data-toast]').classList.remove('shown');

        phone.dataset.phase = 'mark';
        await wait(450, current);

        let present = 0;
        for (const li of register.children) {
            await wait(230, current);
            li.classList.add('marked');
            if (li.classList.contains('present')) {
                present += 1;
                tally.textContent = String(present);
            }
        }
        await wait(350, current);
        flag.classList.add('shown');
        return present;
    }

    async function save(c, present, current) {
        await wait(1200, current);
        const button = $('[data-save]');
        button.classList.add('pressing');
        await wait(160, current);
        button.classList.remove('pressing');
        const toast = $('[data-toast]');
        toast.textContent = `Saved ${c.code}: ${present} of ${c.rows.length} present`;
        toast.classList.add('shown');
        await wait(1900, current);
        toast.classList.remove('shown');
        await wait(400, current);
    }

    async function loop(current) {
        try {
            while (true) {
                const c = CLASSES[next];
                await scan(c, current);
                const present = await mark(c, current);
                await save(c, present, current);
                next = (next + 1) % CLASSES.length;
            }
        } catch (err) {
            if (!(err instanceof Stopped)) throw err;
        }
    }

    // Play only while the phone is on screen, the tab is visible and nobody pressed Pause.
    // A stopped class starts over from its scan when play resumes.
    function update() {
        const shouldRun = onScreen && !paused && !document.hidden;
        if (shouldRun && !run) {
            run = { stopped: false };
            loop(run);
        } else if (!shouldRun && run) {
            run.stopped = true;
            run = null;
        }
    }

    phone.classList.add('is-live');
    toggle.hidden = false;
    toggle.setAttribute('aria-pressed', 'false');
    toggle.addEventListener('click', () => {
        paused = !paused;
        toggle.textContent = paused ? 'Play' : 'Pause';
        toggle.setAttribute('aria-pressed', String(paused));
        update();
    });
    document.addEventListener('visibilitychange', update);
    new IntersectionObserver((entries) => {
        onScreen = entries[entries.length - 1].isIntersecting;
        update();
    }, { threshold: 0.2 }).observe(phone);
}

// Percentages count up from zero alongside their bars
function countUp(el) {
    const target = Number(el.dataset.countTo);
    const started = performance.now();
    const duration = 1000;
    const step = (now) => {
        const t = Math.min(1, (now - started) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = `${Math.round(target * eased)}%`;
        if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

// Sections marked data-animate play their motion (in style.css) once, when they scroll into view
function revealOnScroll() {
    const blocks = document.querySelectorAll('[data-animate]');
    if (reduceMotion) {
        blocks.forEach((block) => block.classList.add('in-view'));
        return;
    }
    // Counters start from zero, so they don't flash their final value before counting up
    document.querySelectorAll('[data-count-to]').forEach((el) => { el.textContent = '0%'; });
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('in-view');
            entry.target.querySelectorAll('[data-count-to]').forEach(countUp);
            observer.unobserve(entry.target);
        });
    }, { threshold: 0.3 });
    blocks.forEach((block) => observer.observe(block));
}

document.addEventListener('DOMContentLoaded', () => {
    heroPhone();
    revealOnScroll();
});
