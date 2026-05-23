import csv
import json

# ── 1. 读取花种换算 ──────────────────────────────────────
seed_rates = {}
with open("flowers.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        flower = row["花朵类型"].strip()
        rate = row["基础产量"].strip()
        if flower and rate:
            seed_rates[flower] = float(rate)

# ── 2. 读取服装列表，按套装分组 ──────────────────────────
outfits_dict = {}
with open("outfits.csv", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    # 去掉所有列名的空格
    reader.fieldnames = [h.strip() for h in reader.fieldnames]
    for row in reader:
        name = row["套装"].strip()
        if name not in outfits_dict:
            outfits_dict[name] = {
                "name": name,
                "location": row["兑换位置"].strip(),
                "parts": []
            }
        outfits_dict[name]["parts"].append({
            "part": row["部件"].strip(),
            "flower": row["所需花朵"].strip(),
            "count": int(row["所需数量"].strip())
        })

outfits = list(outfits_dict.values())

# ── 3. 生成 HTML ─────────────────────────────────────────
data_js = f"""
const SEED_RATES = {json.dumps(seed_rates, ensure_ascii=False)};
const OUTFITS = {json.dumps(outfits, ensure_ascii=False, indent=2)};
"""

html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>服装兑换计算器</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: sans-serif; display: flex; flex-direction: column; height: 100vh; padding: 20px; gap: 16px; }}
    h1 {{ font-size: 20px; }}
    .bonus-row {{ font-size: 15px; }}
    .bonus-row input {{ width: 60px; padding: 4px 8px; font-size: 15px; }}
    .main {{ display: flex; gap: 20px; flex: 1; overflow: hidden; }}
    #outfits {{
      width: 340px;
      flex-shrink: 0;
      overflow-y: auto;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 12px;
    }}
    .right-panel {{
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    button {{ padding: 10px 28px; font-size: 16px; cursor: pointer; border-radius: 6px; width: fit-content; }}
    #result {{
      background: #f5f5f5;
      border-radius: 8px;
      padding: 16px;
      flex: 1;
      overflow-y: auto;
      line-height: 1.8;
    }}
    .outfit {{ border: 1px solid #ddd; border-radius: 8px; margin: 8px 0; padding: 12px; }}
    label {{ cursor: pointer; font-size: 15px; }}
    input[type="checkbox"] {{ margin-right: 8px; width: 16px; height: 16px; cursor: pointer; }}
    .outfit-header {{ display: flex; align-items: center; justify-content: space-between; }}
    .toggle {{ cursor: pointer; padding: 0 8px; color: #666; user-select: none; }}
    .toggle:hover {{ color: #000; }}
    .parts-list {{ margin-top: 8px; padding-left: 16px; border-left: 2px solid #eee; }}
    .part-label {{ display: block; margin: 4px 0; font-size: 13px; color: #444; }}
    .flower-row {{ display: flex; align-items: center; gap: 8px; margin: 8px 0; }}
    .owned-input {{ width: 80px; padding: 4px 8px; font-size: 14px; border: 1px solid #ddd; border-radius: 4px; }}
    .owned-label {{ font-size: 14px; color: #666; }}
  </style>
</head>
<body>
  <h1>服装兑换计算器</h1>
  <div class="bonus-row">
    VIP 产量加成：<input type="number" id="bonus" value="9" min="0"> 朵/颗花种
    &nbsp;&nbsp;
    <label><input type="checkbox" id="rainbow"> 彩虹天（基础产量×2）</label>
  </div>

  <div class="main">
    <div id="outfits"></div>

    <div class="right-panel">
      <button onclick="calculate()">计算</button>
      <button id="calc-seeds-btn" onclick="calculateSeeds()" style="display:none">计算花种</button>
      <div id="result"></div>
    </div>
  </div>
  <script>
    {data_js}

    // 渲染套装列表
    const container = document.getElementById('outfits');
    OUTFITS.forEach((outfit, i) => {{
      const div = document.createElement('div');
      div.className = 'outfit';

      // 套装行：勾选框 + 名字 + toggle箭头
      div.innerHTML = `
        <div class="outfit-header">
          <label>
            <input type="checkbox" class="outfit-cb" data-index="${{i}}">
            <strong>${{outfit.name}}</strong>
            <small style="color:#888; margin-left:8px">${{outfit.location}}</small>
          </label>
          <span class="toggle" data-index="${{i}}">▶</span>
        </div>
        <div class="parts-list" id="parts-${{i}}" style="display:none">
          ${{outfit.parts.map((p, j) => `
            <label class="part-label">
              <input type="checkbox" class="part-cb" data-outfit="${{i}}" data-part="${{j}}"
                data-flower="${{p.flower}}" data-count="${{p.count}}">
              ${{p.part}} — ${{p.flower}} × ${{p.count}}
            </label>`).join('')}}
        </div>`;

      container.appendChild(div);

      // toggle展开/收起
      div.querySelector('.toggle').addEventListener('click', function() {{
        const list = document.getElementById('parts-' + this.dataset.index);
        const open = list.style.display === 'block';
        list.style.display = open ? 'none' : 'block';
        this.textContent = open ? '▶' : '▼';
      }});

      // 勾选整套 → 同步所有部件
      div.querySelector('.outfit-cb').addEventListener('change', function() {{
        const checked = this.checked;
        div.querySelectorAll('.part-cb').forEach(cb => cb.checked = checked);
      }});

      // 勾选部件 → 如果全选则同步套装勾选框
      div.querySelectorAll('.part-cb').forEach(cb => {{
        cb.addEventListener('change', function() {{
          const allParts = div.querySelectorAll('.part-cb');
          const outfitCb = div.querySelector('.outfit-cb');
          const allChecked = [...allParts].every(c => c.checked);
          const anyChecked = [...allParts].some(c => c.checked);
          outfitCb.checked = allChecked;
          outfitCb.indeterminate = anyChecked && !allChecked;
        }});
      }});
    }});

    // 计算
    function calculate() {{
      const totals = {{}};

      document.querySelectorAll('.part-cb:checked').forEach(cb => {{
        const flower = cb.dataset.flower;
        const count = parseInt(cb.dataset.count);
        totals[flower] = (totals[flower] || 0) + count;
      }});

      if (Object.keys(totals).length === 0) {{
        document.getElementById('result').innerHTML = '请先勾选套装或部件';
        return;
      }}

      let html = '<h3>所需花朵</h3>';
      for (const flower in totals) {{
        const need = totals[flower];
        html += `
          <div class="flower-row">
            <span>${{flower}}：需要 ${{need}} 朵</span>
            <input type="number" min="0" value="0"
              class="owned-input"
              data-flower="${{flower}}"
              data-need="${{need}}"
              placeholder="已持有">
            <span class="owned-label">朵</span>
          </div>`;
      }}
      document.getElementById('result').innerHTML = html;
      document.getElementById('calc-seeds-btn').style.display = 'inline-block';
    }}
    function calculateSeeds() {{
      const bonus = parseInt(document.getElementById('bonus').value) || 0;
      const rainbow = document.getElementById('rainbow').checked;

      let html = '<h3>计算结果</h3>';

      document.querySelectorAll('.owned-input').forEach(input => {{
        const flower = input.dataset.flower;
        const need = parseInt(input.dataset.need);
        const owned = parseInt(input.value) || 0;
        const remaining = need - owned;

        if (remaining <= 0) {{
          html += `<p>✅ ${{flower}}：已可兑换</p>`;
        }} else {{
          const rate = SEED_RATES[flower];
          if (rate) {{
            const effectiveRate = (rainbow ? rate * 2 : rate) + bonus;
            const seeds = Math.ceil(remaining / effectiveRate);
            html += `<p>${{flower}}：还差 ${{remaining}} 朵，需要 ${{seeds}} 颗花种</p>`;
          }} else {{
            html += `<p>${{flower}}：还差 ${{remaining}} 朵（花种换算数据暂缺）</p>`;
          }}
        }}
      }});
      document.getElementById('result').innerHTML = html;
    }}
  </script>
</body>
</html>"""

with open("calculator.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ 生成成功！打开 calculator.html 即可使用。")