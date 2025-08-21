# 📝 Word Report Generator with Jinja2 Templating

This project uses [`python-docx-template`](https://docxtpl.readthedocs.io/en/latest/) to generate dynamic `.docx` reports by embedding Jinja2 logic directly into Word templates. It's ideal for creating automated reports, styled documents, and structured tables with conditional formatting.

## 🧩 Using Jinja2 in Word Templates

### 🔧 Basic Syntax

- **Variables**:  
  `{{ name }}` → renders the value of `name` from the context.

- **Control Structures**:

  ```text
  {% if show_paragraph %}
  This paragraph will appear.
  {% endif %}
  ```

- **Loop Metadata**:
  ```text
  {% for item in list %}
  {{ item }}
  {% if not loop.last %}{{ '\f' }}{% endif %}
  {% endfor %}
  ```

### 🧠 Special Tags for Word Structure

To control Word-specific elements like paragraphs and table rows, use extended tags:

| Element      | Syntax Example              |
| ------------ | --------------------------- |
| Paragraph    | `{% p if condition %}`      |
| Table Row    | `{% tr for item in list %}` |
| Table Column | `{% tc if condition %}`     |
| Run (inline) | `{% r if condition %}`      |

These tags ensure proper placement in Word’s XML and remove the tag-containing element after rendering.

### 🎨 RichText Styling

To apply styles dynamically, use `{{ r variable }}` in the template. The variable must be a `RichText` object.

Example:

```text
{{ r styled_text }}
```

### 💬 Comments

Add comments that won’t appear in the final document:

```text
{#p This is a paragraph-level comment #}
{#tr This is a table row comment #}
```

### 🧼 Escaping Special Characters

Avoid XML crashes by escaping `<`, `>`, and `&`:

- Use `{{ var | e }}`
- Or enable autoescaping when rendering

---

## 🎨 Dynamic Cell Coloring in Word Tables

To apply conditional background colors to table cells, use the `{% cellbg %}` tag at the **very beginning of the cell**.

### 📋 Example Table Template

|                                    **Number**                                     |   **Finding**   |         **Risk Score**          |                **Risk**                |
| :-------------------------------------------------------------------------------: | :-------------: | :-----------------------------: | :------------------------------------: |
| **Merged across all 4 columns:** `{%tr for vuln in vulnerabilitiessort_cvss() %}` |                 |                                 |                                        |
|                                 {{ vuln.number }}                                 | {{ vuln.name }} | {% cellbg ... %}{{ vuln.cvss }} | {% cellbg ... %}{{ vuln.risk_rating }} |
|                 **Merged across all 4 columns:** `{%tr endfor %}`                 |                 |                                 |                                        |

### 🎯 Color Codes Used

| Risk Level | Hex Code | Color           |
| ---------- | -------- | --------------- |
| Low        | `93c47d` | Green           |
| Medium     | `ffd966` | Yellow          |
| High       | `e06666` | Red             |
| Unknown    | `ffffff` | White (default) |

---

## ➕ Adding New Fields (Sections) in Word Reports

You can extend your assessment reports with custom fields that are later referenced in the Word template.

### 📋 Steps

1. **Open the Assessment Structure**  
   Choose the section where the new field should appear (e.g., _Summary_, _Additional Fields_, _Vulnerability_).

2. **Create the Field**  
   Enter a clear name for the field (e.g., `risk_notes`) and click **Add new field**. Submit once you're done adding fields.

3. **Locate the Reference**  
   In the **Reporting** tab, you'll find how to reference the field in the Word document.

4. **Use in Word Template**  
   Insert the field with Jinja syntax in your `.docx` template:

   ```text
   {{ section_name.field_name }}
   ```

   **Example:**

   ```text
   {{ summary.risk_notes }}
   ```

### 💡 Tips

- **Case-sensitive:** Field names must match exactly as created.
- **Naming convention:** Use simple, no-space identifiers like `risk_notes`, `impact_level`, `remediation_steps`.
- **Content types:** Fields can store plain text, rich text, or even HTML tables.
- **Styling:** For styled text, pass a `RichText` object and reference it as `{{ r field_name }}`.

### 📑 Rendered Tables vs. Word Template Tables

When adding custom fields that include tables (for example, a **Risk Matrix** or a **Findings table**):

- **Rendered tables** (coming from a field value)  
  These will automatically adopt the **default Word table style** defined in your template.  
  Example: if you add a "Risk Matrix" table as a custom field, when it is rendered in Word it will use the default table formatting of your `.docx` template.

- **Word template tables** (manually created inside the `.docx` template)  
  These will always **keep the formatting and styling you applied** in Word (borders, shading, fonts, etc.).  
  Example: if you insert a pre-styled "Mitigation Steps" table directly in the Word template, it will retain your custom colors and layout.

👉 **In short:**

- Tables **from custom fields** = inherit the default Word table style.
- Tables **built directly in Word** = retain their custom design and formatting.

---

## 🧠 Advanced Template Usage

### 🔍 Custom Filters

Your template uses filters like:

```text
{{ vulnerabilities|count_risk_rating('Critical') }}
```

This requires defining a custom Jinja2 filter in your Python code.

### 📄 Page Breaks

To insert a page break between items:

```text
{% if not loop.last %}{{ '\f' }}{% endif %}
```

`\f` is interpreted as a page break when used inside a string variable.

### 🧬 Nested Object Access

Your template uses dot notation for nested data:

```text
{{ client.name }}
{{ vuln.fields.Reference }}
```

This works for dictionaries and objects alike.

### 🔖 Bookmark Insertion

To insert a Word bookmark dynamically, use the `++bookmark<name>` syntax directly after the content:

```text
{{vuln.number}} – {{vuln.name}} ++bookmark{{vuln.number}}
```

- This creates a bookmark named `vuln.number` at that location.
- Useful for linking, navigation, or referencing sections programmatically.

---

## 📚 References

- Full documentation: [python-docx-template docs](https://docxtpl.readthedocs.io/en/latest/)
