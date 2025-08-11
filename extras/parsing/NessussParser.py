import csv

with open(r'C:\Users\Ahtro\Desktop\Threat_Track\extras\parsing\nessess.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # skip header row
    for row in reader:
        if len(row) >= 8:  # check that row has at least 8 elements
            plugin_id = row[0]
            cve = row[1]
            cvss_score = row[2]
            risk = row[3]
            host = row[4]
            protocol = row[5]
            port = row[6]
            name = row[7]
            print(f"Plugin ID: {plugin_id}\nCVE: {cve}\nCVSS Score: {cvss_score}\nRisk: {risk}\nHost: {host}\nProtocol: {protocol}\nPort: {port}\nName: {name}\n")
        else:
            print(f"Row {row} has less than 8 elements")
