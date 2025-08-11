import xml.etree.ElementTree as ET
tree = ET.parse(r'C:\Users\Ahtro\Desktop\Threat_Track\reporting\cwe.xml')
root = tree.getroot()
ns = {'cwe': 'http://cwe.mitre.org/cwe-6'}

for weakness in root.findall('.//cwe:Weakness', ns):
    
    name = weakness.attrib['Name']
    id = weakness.attrib['ID']
    description = weakness.find('cwe:Description', ns).text
    
    # Get impact notes and added to list of impact_notes
    impacts = weakness.findall('.//cwe:Common_Consequences/cwe:Consequence', ns)
    impact_notes = []
    
    for impact in impacts:
        if impact.find('cwe:Note', ns) is not None:
            note = impact.find('cwe:Note', ns).text
            impact_notes.append(note)


    # Get mitigations and added to list of mitigation_notes
    mitigations = weakness.findall('.//cwe:Potential_Mitigations/cwe:Mitigation', ns)
    mitigation_notes = []
    
    for mitigation in mitigations:
        if mitigation.find('cwe:Description', ns) is not None:
            effectiveness_note = mitigation.find('cwe:Description', ns).text
            mitigation_notes.append(effectiveness_note)
    
    results = {'vulnerability_name':name, 'id':id, 'description':description}

    if len(impact_notes) > 0:
        notes_to_add = ''
        for i in range(len(impact_notes)):
            if i == len(impact_notes) -1:
                notes_to_add = notes_to_add + impact_notes[i]
            else:
                notes_to_add = notes_to_add + impact_notes[i] + '\n'
        results['impact_notes']= notes_to_add
    
    
    if len(mitigation_notes) > 0:
        m_to_add = ''
        for m_note in mitigation_notes:
            m_to_add = str(m_to_add) + str(m_note)  + '\n'
        results['mitigation_notes'] = m_to_add.strip()


    
    new_vulnerability = Vulnerability(name=results['vulnerability_name'], tag='CWE-' + str(results['id']), description= results['description'])
    
    if results.get('impact_notes') is not None:
        new_vulnerability.impact = results['impact_notes']
                    
    if results.get('mitigation_notes') is not None:
        new_vulnerability.remediation = results['mitigation_notes']
    
    new_vulnerability.save() 