def build_html(data_js):
    return f"""<!DOCTYPE html>
    <html lang="zh">
    <head>
      <meta charset="UTF-8">
      <title>服装兑换计算器</title>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
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
        .location-group {{ border: 1px solid #bbb; border-radius: 8px; margin: 8px 0; padding: 12px; background: #fafafa; }}
        .location-header {{ display: flex; align-items: center; justify-content: space-between; }}
        .location-list {{ margin-top: 8px; padding-left: 12px; }}
        .result-item {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 10px 14px; margin: 8px 0; line-height: 2; }}
        .result-item small {{ color: #666; font-size: 13px; }}
      </style>
    </head>
    <body>
      <h1>服装兑换计算器</h1>
      <div class="bonus-row">
        奇妙花宝产量加成：<input type="number" id="bonus" value="9" min="0"> 朵/颗花种
        &nbsp;&nbsp;
        <label><input type="checkbox" id="rainbow"> 彩虹天（基础产量×2）</label>
        &nbsp;&nbsp;
        <label>上传背包：<input type="file" id="bag-upload" accept=".xlsx"></label>
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
        
        let bagFlowers = Object.assign({{}}, DEFAULT_BAG_FLOWERS);
        let bagSeeds = Object.assign({{}}, DEFAULT_BAG_SEEDS);

        document.getElementById('bag-upload').addEventListener('change', function(e) {{
          const file = e.target.files[0];
          if (!file) return;
          const reader = new FileReader();
          reader.onload = function(e) {{
            const workbook = XLSX.read(e.target.result, {{type: 'array'}});
            const ws = workbook.Sheets[workbook.SheetNames[0]];
            const rows = XLSX.utils.sheet_to_json(ws);
            bagFlowers = {{}};
            bagSeeds = {{}};
            rows.forEach(row => {{
              const flower = (row['花朵类型'] || '').toString().trim();
              if (flower) {{
                bagFlowers[flower] = parseInt(row['花朵数量']) || 0;
                bagSeeds[flower] = parseInt(row['花种数量']) || 0;
              }}
            }});
            document.querySelectorAll('.owned-input').forEach(input => {{
              const flower = input.dataset.flower;
              if (bagFlowers[flower] !== undefined) {{
                input.value = bagFlowers[flower];
              }}
            }});
          }};
          reader.readAsArrayBuffer(file);
        }});

        const container = document.getElementById('outfits');
        LOCATIONS.forEach((locGroup, li) => {{
          const locDiv = document.createElement('div');
          locDiv.className = 'location-group';
          locDiv.innerHTML = `
            <div class="location-header">
              <label>
                <input type="checkbox" class="location-cb" data-loc="${{li}}">
                <strong>${{locGroup.location}}</strong>
              </label>
              <span class="toggle" data-target="loc-${{li}}">▶</span>
            </div>
            <div class="location-list" id="loc-${{li}}" style="display:none"></div>`;
          container.appendChild(locDiv);

          const locationList = document.getElementById('loc-' + li);
          locGroup.outfits.forEach((outfit, oi) => {{
            const partsId = `parts-${{li}}-${{oi}}`;
            const outfitDiv = document.createElement('div');
            outfitDiv.className = 'outfit';
            outfitDiv.innerHTML = `
              <div class="outfit-header">
                <label>
                  <input type="checkbox" class="outfit-cb" data-loc="${{li}}" data-outfit="${{oi}}">
                  <strong>${{outfit.name}}</strong>
                </label>
                <span class="toggle" data-target="${{partsId}}">▶</span>
              </div>
              <div class="parts-list" id="${{partsId}}" style="display:none">
                ${{outfit.parts.map((p, pi) => `
                  <label class="part-label">
                    <input type="checkbox" class="part-cb"
                      data-loc="${{li}}" data-outfit="${{oi}}" data-part="${{pi}}"
                      data-flower="${{p.flower}}" data-count="${{p.count}}">
                    ${{p.part}} — ${{p.flower}} × ${{p.count}}
                  </label>`).join('')}}
              </div>`;
            locationList.appendChild(outfitDiv);

            outfitDiv.querySelector('.outfit-cb').addEventListener('change', function() {{
              outfitDiv.querySelectorAll('.part-cb').forEach(cb => cb.checked = this.checked);
              syncLocationCb(li);
            }});
            outfitDiv.querySelectorAll('.part-cb').forEach(cb => {{
              cb.addEventListener('change', function() {{
                const allParts = outfitDiv.querySelectorAll('.part-cb');
                const outfitCb = outfitDiv.querySelector('.outfit-cb');
                const allChecked = [...allParts].every(c => c.checked);
                const anyChecked = [...allParts].some(c => c.checked);
                outfitCb.checked = allChecked;
                outfitCb.indeterminate = anyChecked && !allChecked;
                syncLocationCb(li);
              }});
            }});
          }});

          locDiv.querySelector('.location-cb').addEventListener('change', function() {{
            locDiv.querySelectorAll('.outfit-cb, .part-cb').forEach(cb => {{
              cb.checked = this.checked;
              cb.indeterminate = false;
            }});
          }});
        }});

        document.addEventListener('click', function(e) {{
          if (e.target.classList.contains('toggle')) {{
            const target = document.getElementById(e.target.dataset.target);
            if (!target) return;
            const open = target.style.display === 'block';
            target.style.display = open ? 'none' : 'block';
            e.target.textContent = open ? '▶' : '▼';
          }}
        }});

        function syncLocationCb(li) {{
          const locDiv = container.children[li];
          const allParts = locDiv.querySelectorAll('.part-cb');
          const locCb = locDiv.querySelector('.location-cb');
          const allChecked = [...allParts].every(c => c.checked);
          const anyChecked = [...allParts].some(c => c.checked);
          locCb.checked = allChecked;
          locCb.indeterminate = anyChecked && !allChecked;
        }}

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
                <input type="number" min="0" value="${{bagFlowers[flower] || 0}}"
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
                const source = FLOWER_SOURCES[flower] ? `获取方式：${{FLOWER_SOURCES[flower]}}` : '获取方式：暂无可用信息';
                let timeStr = '暂无可用信息';
                const totalMins = FLOWER_TIMES[flower];
                if (totalMins) {{
                  const hours = Math.floor(totalMins / 60);
                  const mins = totalMins % 60;
                  timeStr = hours > 0 ? `${{hours}} 小时 ${{mins}} 分钟` : `${{mins}} 分钟`;
                }}
                
                const ownedSeeds = bagSeeds[flower] || 0;
                const seedsToBuy = Math.max(0, seeds - ownedSeeds);

                let costStr = '';
                const price = FLOWER_PRICES[flower];
                const unit = FLOWER_UNITS[flower];
                if (seedsToBuy > 0 && price && unit) {{
                  const totalCost = Math.ceil(seedsToBuy * price);
                  costStr = `<small>💰 共需资源：${{totalCost}} ${{unit}}</small><br>`;
                }}

                let seedStr = '';
                if (seedsToBuy <= 0) {{
                  seedStr = `<small>🌱 花种已足够，无需兑换（背包已有 ${{ownedSeeds}} 颗）</small><br>`;
                }} else {{
                  seedStr = `<small>🌱 需种 ${{seeds}} 颗，背包已有 ${{ownedSeeds}} 颗，还需兑换 ${{seedsToBuy}} 颗</small><br>`;
                }}

                html += `
                  <div class="result-item">
                    <p><strong>${{flower}}</strong>：还差 ${{remaining}} 朵，需要种 ${{seeds}} 颗花种</p>
                    ${{seedStr}}
                    <small>⏱ 开花时间：${{timeStr}}</small><br>
                    <small>📍 ${{source}}</small><br>
                    ${{costStr}}
                  </div>`;
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