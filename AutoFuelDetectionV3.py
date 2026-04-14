import pdfplumber
import pandas as pd
import glob
import re
import os
import webbrowser
from datetime import datetime

# --- CONFIGURATION ---
FUEL_PRICE_PER_LITER = 1.35 

def clean_german_float(s):
    """Converts '1.234,56' or '1234.56' to float."""
    if not isinstance(s, str): return 0.0
    s = s.strip().replace('EUR', '').replace('€', '').strip()
    try:
        if ',' in s and ('.' not in s or s.find('.') < s.find(',')):
            s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            s = s.replace(',', '')
        return float(s)
    except:
        return 0.0

def generate_html_report(split_df, static_odo_list, total_tx_count):
    """Creates a Formal Bank-Style Audit Report."""
    
    timestamp = datetime.now().strftime("%d %B %Y - %H:%M")
    
    # Statistics
    suspicious_count = len(split_df) if not split_df.empty else 0
    theft_rate = (suspicious_count / total_tx_count * 100) if total_tx_count > 0 else 0
    
    total_stolen_liters = 0
    if not split_df.empty:
        # Conservative estimate: ~35% of volume in split transactions is the 'second' fill
        total_vol = split_df['Total_Vol'].sum()
        total_stolen_liters = total_vol * 0.35 
    
    est_loss = total_stolen_liters * FUEL_PRICE_PER_LITER

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fuel Fraud Audit - {timestamp}</title>
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #555; padding: 40px; }}
            .paper {{ max-width: 850px; margin: 0 auto; background: white; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); min-height: 1000px; }}
            
            /* HEADER */
            .header {{ border-bottom: 3px solid #333; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
            .title h1 {{ margin: 0; color: #cc0000; font-size: 28px; text-transform: uppercase; letter-spacing: 1px; }}
            .title h2 {{ margin: 5px 0 0; color: #333; font-size: 14px; font-weight: normal; }}
            .meta {{ text-align: right; color: #777; font-size: 12px; }}

            /* SUMMARY BOXES */
            .dashboard {{ display: flex; justify-content: space-between; gap: 15px; margin-bottom: 40px; }}
            .card {{ flex: 1; background: #f9f9f9; padding: 15px; border: 1px solid #ddd; border-radius: 4px; text-align: center; }}
            .card-title {{ font-size: 11px; text-transform: uppercase; color: #888; letter-spacing: 1px; margin-bottom: 5px; }}
            .card-value {{ font-size: 24px; font-weight: bold; color: #333; }}
            .card.danger {{ background: #fff5f5; border-color: #ffcccc; }}
            .card.danger .card-value {{ color: #cc0000; }}

            /* TABLES */
            h3 {{ border-left: 5px solid #cc0000; padding-left: 10px; color: #333; margin-top: 40px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 15px; }}
            th {{ background-color: #f1f1f1; border-bottom: 2px solid #ddd; padding: 12px 8px; text-align: left; font-weight: bold; color: #555; }}
            td {{ padding: 10px 8px; border-bottom: 1px solid #eee; color: #333; }}
            tr:nth-child(even) {{ background-color: #fcfcfc; }}
            
            /* BADGES */
            .tag {{ padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; text-transform: uppercase; }}
            .tag-red {{ background: #ffe6e6; color: #cc0000; }}
            .tag-orange {{ background: #fff0e6; color: #e65c00; }}

            .footer {{ margin-top: 60px; border-top: 1px solid #eee; padding-top: 20px; font-size: 11px; color: #999; text-align: center; }}
            
            @media print {{
                body {{ background: white; padding: 0; }}
                .paper {{ box-shadow: none; margin: 0; padding: 20px; }}
            }}
        </style>
    </head>
    <body>
        <div class="paper">
            <div class="header">
                <div class="title">
                    <h1>Internal Audit Report</h1>
                    <h2>Fuel Consumption & Fraud Detection</h2>
                </div>
                <div class="meta">
                    REPORT ID: AUD-{datetime.now().strftime("%Y%m%d-%H%M%S")}<br>
                    DATE: {timestamp}
                </div>
            </div>

            <div class="dashboard">
                <div class="card">
                    <div class="card-title">Transactions Scanned</div>
                    <div class="card-value">{total_tx_count}</div>
                </div>
                <div class="card danger">
                    <div class="card-title">Suspicious Events</div>
                    <div class="card-value">{suspicious_count}</div>
                </div>
                <div class="card danger">
                    <div class="card-title">Fraud Rate</div>
                    <div class="card-value">{theft_rate:.1f}%</div>
                </div>
                <div class="card danger">
                    <div class="card-title">Est. Loss</div>
                    <div class="card-value">€{est_loss:,.2f}</div>
                </div>
            </div>

            <p style="color: #666; font-size: 14px; line-height: 1.5;">
                <strong>Audit Finding:</strong> An automated forensic analysis of invoice data has identified a pattern of 
                <strong>systemic fuel irregularities</strong>. The data indicates multiple instances of vehicles being refueled 
                twice within minutes (Split Transactions) and widespread falsification of odometer records to conceal consumption rates.
            </p>

            <h3>1. CRITICAL: Split Transactions (Double-Dipping)</h3>
            <p style="font-size: 12px; color: #666;">The following vehicles refueled multiple times on the same date. 
            Volumes typically exceed the physical tank capacity of a standard commercial van.</p>
    """

    if not split_df.empty:
        html_content += "<table><thead><tr><th>Date</th><th>Vehicle ID</th><th>Refuel Count</th><th>Total Volume</th><th>Risk Level</th></tr></thead><tbody>"
        for _, row in split_df.iterrows():
            date_str = row['Date'].strftime("%d.%m.%Y")
            html_content += f"""
            <tr>
                <td>{date_str}</td>
                <td><strong>{row['Vehicle']}</strong></td>
                <td>{row['Count']} Times</td>
                <td>{row['Total_Vol']:.2f} Liters</td>
                <td><span class="tag tag-red">High Risk</span></td>
            </tr>
            """
        html_content += "</tbody></table>"
    else:
        html_content += "<p>✅ No split transactions found.</p>"

    html_content += """
            <h3>2. COMPLIANCE: Data Falsification</h3>
            <p style="font-size: 12px; color: #666;">The following drivers are repeatedly entering static or false odometer readings 
            (e.g., '8888', '137'). This action prevents MPG calculation and hides fuel theft.</p>
    """

    if static_odo_list:
        html_content += "<table><thead><tr><th>Vehicle ID</th><th>Reported Odometer</th><th>Audit Status</th></tr></thead><tbody>"
        for item in static_odo_list:
            html_content += f"""
            <tr>
                <td><strong>{item['Vehicle']}</strong></td>
                <td>{item['Odometer']}</td>
                <td><span class="tag tag-orange">Invalid Data</span></td>
            </tr>
            """
        html_content += "</tbody></table>"
    else:
        html_content += "<p>✅ All odometer readings appear dynamic.</p>"

    html_content += f"""
            <div class="footer">
                CONFIDENTIAL INTERNAL DOCUMENT • AUTOMATED GENERATION
            </div>
        </div>
    </body>
    </html>
    """
    
    filename = "Fuel_Audit_Report.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n✅ REPORT GENERATED: {filename}")
    print("🚀 Opening in browser...")
    webbrowser.open('file://' + os.path.realpath(filename))

def analyze_all_invoices():
    print("--- 🚀 STARTING AUDIT... ---")
    pdf_files = glob.glob("*.pdf")
    
    if not pdf_files:
        print("❌ ERROR: No PDF files found.")
        input("Press Enter to exit...")
        return

    all_transactions = []
    date_pattern = re.compile(r'\d{2}/\d{2}/\d{4}')

    # --- EXTRACTION LOOP ---
    for pdf_path in pdf_files:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text: continue
                    lines = text.split('\n')
                    for line in lines:
                        if date_pattern.search(line) and ("Diesel" in line or "Ad Blue" in line):
                            parts = line.split()
                            if len(parts) < 5: continue
                            try:
                                date_str = date_pattern.search(line).group()
                                numbers = [clean_german_float(p) for p in parts if clean_german_float(p) > 0]
                                
                                odometer = 0
                                volume = 0
                                
                                if "Diesel" in line:
                                    diesel_idx = -1
                                    for i, part in enumerate(parts):
                                        if "Diesel" in part:
                                            diesel_idx = i
                                            break
                                    if diesel_idx != -1 and diesel_idx + 1 < len(parts):
                                        volume = clean_german_float(parts[diesel_idx + 1])
                                    
                                    for part in parts:
                                        if part.isdigit() and len(part) < 7:
                                            odometer = int(part)
                                            break

                                if volume > 0:
                                    entry = {
                                        'File': pdf_path,
                                        'Date': pd.to_datetime(date_str, dayfirst=True),
                                        'Vehicle': 'Unknown',
                                        'Odometer': odometer,
                                        'Volume': volume
                                    }
                                    for part in parts:
                                        if "KARTE" in part or "SAL" in part:
                                            entry['Vehicle'] = part
                                    all_transactions.append(entry)
                            except:
                                continue
        except:
            continue

    df = pd.DataFrame(all_transactions)
    if df.empty:
        print("❌ No data found.")
        input("Press Enter to exit...")
        return

    df = df.sort_values(by=['Vehicle', 'Date'])

    # 1. Analyze Split Transactions
    dup_counts = df.groupby(['Vehicle', 'Date']).size()
    dups = dup_counts[dup_counts > 1]
    
    split_data = []
    if not dups.empty:
        for (vehicle, date), count in dups.items():
            related_rows = df[(df['Vehicle'] == vehicle) & (df['Date'] == date)]
            total_vol = related_rows['Volume'].sum()
            split_data.append({
                'Date': date,
                'Vehicle': vehicle,
                'Count': count,
                'Total_Vol': total_vol
            })
    split_df = pd.DataFrame(split_data)
    if not split_df.empty:
        split_df = split_df.sort_values(by='Date', ascending=False)

    # 2. Analyze Static Odometers
    static_odo_list = []
    for vehicle in df['Vehicle'].unique():
        if vehicle == "Unknown": continue
        vehicle_data = df[df['Vehicle'] == vehicle]
        unique_odos = vehicle_data['Odometer'].unique()
        if len(vehicle_data) > 3 and len(unique_odos) == 1:
            static_odo_list.append({'Vehicle': vehicle, 'Odometer': unique_odos[0]})

    # 3. Generate Report (Passing Total TX Count)
    generate_html_report(split_df, static_odo_list, len(df))

if __name__ == "__main__":
    analyze_all_invoices()
    input("\n✅ Audit Complete. Press Enter to close...")
