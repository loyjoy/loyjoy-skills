/*
 * LoyJoy web component starter
 *
 * Two patterns for WEB_COMPONENT_SUBPROCESS modules, in one bundle:
 *   <lj-configurator>  all inputs on one card, live result, one primary button
 *   <lj-compare>       two or three options side by side, select one, continue
 *
 * Contract with LoyJoy
 *   Input:  prop mappings (type="prop") arrive as a JSON object on the
 *           `properties` property or attribute. Pass `lang` via
 *           source_expression="displayLanguage()".
 *   Output: dispatch CustomEvent('variables', { detail: { variables, continue: true },
 *           bubbles: true, composed: true }). LoyJoy stores every key scoped as
 *           <key>_<module id with non-alphanumerics replaced by _>.
 *
 * Adapt BRAND, TEXT, the inputs and the recommend() logic. Keep the lock-after-submit
 * behaviour. Mark example figures as indicative on the card.
 */
(function () {
  var BRAND = { accent: '#2949A0', accentDark: '#1F3780', ink: '#1E1E2D', muted: '#6B6B80', line: '#E6E6F0', soft: '#F3F4FA', ok: '#2BB673' }

  var TEXT = {
    en: { title: 'Find your plan', household: 'Who is covered?', me: 'Me', couple: 'Me + partner', age: 'Age', needs: 'Your needs', low: 'Low', mid: 'Medium', high: 'High', result: 'Recommended', from: 'from', month: '/ month', cta: 'Continue', done: 'Saved', note: 'Example figures, indicative only.', compare: 'Compare the options', choose: 'Continue with', badge: 'For you' },
    de: { title: 'Ihr passender Tarif', household: 'Wer ist versichert?', me: 'Ich', couple: 'Ich + Partner', age: 'Alter', needs: 'Ihr Bedarf', low: 'Gering', mid: 'Mittel', high: 'Hoch', result: 'Empfehlung', from: 'ab', month: '/ Monat', cta: 'Weiter', done: 'Gespeichert', note: 'Beispielwerte, unverbindlich.', compare: 'Optionen vergleichen', choose: 'Weiter mit', badge: 'Für Sie' }
  }

  // Example catalogue. Replace with the customer's public data.
  var OPTIONS = [
    { id: 'basic', name: 'Basic', price: 20, a: 100, b: 200 },
    { id: 'plus', name: 'Plus', price: 35, a: 200, b: 400 },
    { id: 'premium', name: 'Premium', price: 55, a: 300, b: 700 }
  ]

  function readProps (el) {
    var p = el._props || el.getAttribute('properties')
    try { if (typeof p === 'string') p = JSON.parse(p) } catch (e) { p = null }
    return p || {}
  }
  function lang (p) {
    var l = String(p.lang || document.documentElement.lang || navigator.language || 'en').toLowerCase()
    return TEXT[l.slice(0, 2)] ? l.slice(0, 2) : 'en'
  }
  function emit (el, vars) {
    el.dispatchEvent(new CustomEvent('variables', { detail: { variables: vars, continue: true }, bubbles: true, composed: true }))
  }
  function eur (n) { return Math.round(n) + ' €' }

  var BASE_CSS = [
    ':host{display:block;font-family:inherit;color:' + BRAND.ink + ';-webkit-font-smoothing:antialiased}',
    '*{box-sizing:border-box}button{font:inherit;cursor:pointer}',
    '.card{max-width:440px;margin:0 auto;background:#fff;border:1px solid ' + BRAND.line + ';border-radius:22px;overflow:hidden;box-shadow:0 6px 24px rgba(30,30,60,.08)}',
    '.hd{padding:16px 18px 6px;font-weight:700;font-size:17px}',
    '.sec{padding:8px 18px}.lab{font-size:12px;color:' + BRAND.muted + ';margin:6px 0;font-weight:600}',
    '.seg{display:grid;gap:6px}.seg button{border:1px solid ' + BRAND.line + ';background:#fff;border-radius:12px;padding:8px 4px;font-size:12.5px;color:' + BRAND.ink + '}',
    '.seg button[aria-pressed="true"]{background:' + BRAND.accent + ';border-color:' + BRAND.accent + ';color:#fff}',
    '.res{margin:10px 12px 4px;border-radius:18px;background:' + BRAND.accent + ';color:#fff;padding:14px 16px}',
    '.rl{font-size:11.5px;opacity:.85;text-transform:uppercase;font-weight:600}.rn{font-size:26px;font-weight:800}.rp b{font-size:18px}',
    '.ctaw{padding:12px 18px 0}.cta{width:100%;border:0;border-radius:999px;background:' + BRAND.accent + ';color:#fff;font-weight:700;font-size:15px;padding:13px}',
    '.cta:disabled{background:' + BRAND.ok + ';cursor:default}',
    '.note{font-size:10.5px;color:' + BRAND.muted + ';padding:10px 18px 14px}',
    '.locked .ctl{pointer-events:none;opacity:.6}',
    'input[type=range]{accent-color:' + BRAND.accent + '}'
  ].join('')

  function seg (id, opts) {
    var h = '<div class="seg ctl" id="' + id + '" style="grid-template-columns:repeat(' + opts.length + ',1fr)">'
    opts.forEach(function (o) { h += '<button type="button" data-v="' + o[0] + '">' + o[1] + '</button>' })
    return h + '</div>'
  }

  /* ---------------------------------------------------------------- configurator */

  function recommend (s) {
    var idx = { low: 0, mid: 1, high: 2 }[s.needs] || 0
    if (s.household === 'couple' && idx < 1) idx = 1
    return idx
  }

  class LjConfigurator extends HTMLElement {
    static get observedAttributes () { return ['properties'] }
    constructor () { super(); this.attachShadow({ mode: 'open' }); this.s = { household: 'me', age: 35, needs: 'low' }; this._done = false }
    set properties (v) { this._props = v; this.applyProps(); if (this._built) this.update() }
    get properties () { return this._props }
    attributeChangedCallback () { this.applyProps(); if (this._built) this.update() }
    connectedCallback () { this.applyProps(); if (!this._built) this.build(); this.update() }

    // Pre-fill from props, e.g. values the AI agent saved from free text.
    applyProps () {
      if (this._done) return
      var p = readProps(this)
      this.T = TEXT[lang(p)]
      if (p.household === 'me' || p.household === 'couple') this.s.household = p.household
      var a = parseInt(p.age, 10); if (!isNaN(a) && a >= 16 && a <= 99) this.s.age = a
      if (['low', 'mid', 'high'].indexOf(p.needs) >= 0) this.s.needs = p.needs
    }

    build () {
      this._built = true
      var self = this; var T = this.T
      var h = '<style>' + BASE_CSS + '</style><div class="card"><div class="hd">' + T.title + '</div>'
      h += '<div class="sec"><div class="lab">' + T.household + '</div>' + seg('household', [['me', T.me], ['couple', T.couple]]) + '</div>'
      h += '<div class="sec"><div class="lab">' + T.age + ': <b id="age"></b></div><input class="ctl" id="ageIn" type="range" min="18" max="90" style="width:100%"></div>'
      h += '<div class="sec"><div class="lab">' + T.needs + '</div>' + seg('needs', [['low', T.low], ['mid', T.mid], ['high', T.high]]) + '</div>'
      h += '<div class="res"><div class="rl">' + T.result + '</div><div class="rn" id="rn"></div><div class="rp">' + T.from + ' <b id="rp"></b> ' + T.month + '</div></div>'
      h += '<div class="ctaw"><button type="button" class="cta" id="cta">' + T.cta + ' →</button></div><div class="note">' + T.note + '</div></div>'
      this.shadowRoot.innerHTML = h
      var $ = this.$ = function (id) { return self.shadowRoot.getElementById(id) }
      ;['household', 'needs'].forEach(function (k) {
        $(k).querySelectorAll('button').forEach(function (b) { b.addEventListener('click', function () { if (!self._done) { self.s[k] = b.getAttribute('data-v'); self.update() } }) })
      })
      $('ageIn').addEventListener('input', function () { self.s.age = Number(this.value); self.update() })
      $('cta').addEventListener('click', function () { self.finish() })
    }

    update () {
      var s = this.s; var $ = this.$
      ;['household', 'needs'].forEach(function (k) { $(k).querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-v') === s[k])) }) })
      $('age').textContent = s.age; $('ageIn').value = s.age
      var o = OPTIONS[recommend(s)]
      $('rn').textContent = o.name; $('rp').textContent = eur(o.price)
    }

    finish () {
      if (this._done) return
      this._done = true
      var b = this.$('cta'); b.disabled = true; b.textContent = this.T.done + ' ✓'
      this.shadowRoot.querySelector('.card').classList.add('locked')
      var o = OPTIONS[recommend(this.s)]
      emit(this, { household: this.s.household, age: String(this.s.age), needs: this.s.needs, option: o.id })
    }
  }
  if (!customElements.get('lj-configurator')) customElements.define('lj-configurator', LjConfigurator)

  /* ---------------------------------------------------------------- comparison */

  var CMP_CSS = BASE_CSS + [
    '.cols{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:8px 14px}',
    '.col{position:relative;border:1px solid ' + BRAND.line + ';border-radius:16px;padding:12px 8px;text-align:center;background:#fff}',
    '.col[aria-pressed="true"]{border-color:' + BRAND.accent + ';box-shadow:0 0 0 2px ' + BRAND.accent + ' inset}',
    '.badge{position:absolute;top:-9px;left:50%;transform:translateX(-50%);background:' + BRAND.ok + ';color:#fff;font-size:10px;font-weight:700;border-radius:99px;padding:2px 8px;white-space:nowrap}',
    '.cn{font-weight:800}.cp{color:' + BRAND.accent + ';font-weight:800;font-size:20px;margin-top:4px}',
    '.row{display:flex;justify-content:space-between;font-size:11px;padding:3px 0;border-top:1px solid ' + BRAND.line + ';margin-top:6px}'
  ].join('')

  class LjCompare extends HTMLElement {
    static get observedAttributes () { return ['properties'] }
    constructor () { super(); this.attachShadow({ mode: 'open' }); this._done = false }
    set properties (v) { this._props = v; this.init(); if (this._built) this.update() }
    get properties () { return this._props }
    attributeChangedCallback () { this.init(); if (this._built) this.update() }
    connectedCallback () { this.init(); if (!this._built) this.build(); this.update() }

    init () {
      if (this._done) return
      var p = readProps(this)
      this.T = TEXT[lang(p)]
      var r = OPTIONS.map(function (o) { return o.id }).indexOf(p.option)
      this.rec = r < 0 ? 1 : r
      if (this.sel === undefined) this.sel = this.rec
    }

    build () {
      this._built = true
      var self = this
      this.shadowRoot.innerHTML = '<style>' + CMP_CSS + '</style><div class="card"><div class="hd">' + this.T.compare + '</div><div class="cols ctl" id="cols"></div><div class="ctaw"><button type="button" class="cta" id="cta"></button></div><div class="note">' + this.T.note + '</div></div>'
      this.$ = function (id) { return self.shadowRoot.getElementById(id) }
      this.$('cta').addEventListener('click', function () { self.finish() })
    }

    update () {
      var self = this; var T = this.T; var h = ''
      OPTIONS.forEach(function (o, i) {
        h += '<button type="button" class="col" data-i="' + i + '" aria-pressed="' + (i === self.sel) + '">'
        if (i === self.rec) h += '<span class="badge">' + T.badge + '</span>'
        h += '<div class="cn">' + o.name + '</div><div class="cp">' + eur(o.price) + '</div>'
        h += '<div class="row"><span>A</span><b>' + o.a + ' %</b></div><div class="row"><span>B</span><b>' + eur(o.b) + '</b></div></button>'
      })
      this.$('cols').innerHTML = h
      this.$('cols').querySelectorAll('.col').forEach(function (b) { b.addEventListener('click', function () { if (!self._done) { self.sel = Number(b.getAttribute('data-i')); self.update() } }) })
      if (!this._done) this.$('cta').textContent = T.choose + ' ' + OPTIONS[this.sel].name + ' →'
    }

    finish () {
      if (this._done) return
      this._done = true
      var o = OPTIONS[this.sel]
      var b = this.$('cta'); b.disabled = true; b.textContent = o.name + ' ✓'
      this.shadowRoot.querySelector('.card').classList.add('locked')
      emit(this, { option: o.id, price: String(o.price) })
    }
  }
  if (!customElements.get('lj-compare')) customElements.define('lj-compare', LjCompare)
})()
