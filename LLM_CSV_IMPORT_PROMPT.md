# 🤖 LLM Prompt Guide for SpellMaster CSV Import

Use the prompt templates below with any LLM (ChatGPT, Claude, Gemini, DeepSeek) to instantly generate perfectly structured spelling word lists with kid-friendly context sentences that can be directly uploaded or pasted into the **SpellMaster Admin Portal** (`/admin/import`).

---

## 📋 Required CSV Format

The CSV Import module expects 4 columns (comma-separated):

| Column | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `folder` | Yes | The top-level bundle / grade folder | `4th Grade Non-Negotiable` |
| `list_title` | Yes | The name of the specific list | `List 1 (Aug 28th)` |
| `word` | Yes | The spelling word or phrase | `believe` or `didn't` |
| `context_sentence` | Recommended | A kid-friendly sentence containing the word | `I believe you can do it.` |

---

## 🚀 Copy-and-Paste LLM Prompts

### Prompt 1: Convert an Existing Word List into CSV with Context Sentences
> **Use Case**: When you have a list of words from school, a PDF, or a photo and want the LLM to write kid-friendly context sentences for them.

```markdown
You are an expert elementary school curriculum assistant. 
Please convert the following list of spelling words into a clean CSV format for my spelling app.

[PASTE YOUR WORDS HERE]

Folder Name: [e.g. 4th Grade Non-Negotiable]
List Title: [e.g. List 1 (Aug 28th)]

Output Requirements:
1. Provide the output STRICTLY as raw CSV text (do NOT include markdown code blocks, explanations, or conversational text).
2. The first line MUST be the header:
folder,list_title,word,context_sentence
3. For every word, generate a natural, engaging, kid-friendly context sentence (elementary school level) that clearly demonstrates the word's meaning.
4. For homophones or contractions (e.g. hear/here, their/there/they're, it's/its, didn't), make sure the sentence clearly distinguishes the intended meaning.
5. If a sentence contains commas or quotation marks, wrap the sentence in double quotes.

Example Output:
folder,list_title,word,context_sentence
4th Grade Non-Negotiable,List 1 (Aug 28th),about,"We read a fascinating story about dolphins."
4th Grade Non-Negotiable,List 1 (Aug 28th),addition,"In addition to math, we practice spelling every day."
4th Grade Non-Negotiable,List 1 (Aug 28th),believe,"I believe you can accomplish anything with practice."
4th Grade Non-Negotiable,List 1 (Aug 28th),didn't,"He didn't forget his homework folder today."
```

---

### Prompt 2: Generate a Brand New Grade-Level Vocabulary List
> **Use Case**: When you want the LLM to create a full set of themed spelling lists from scratch (e.g. 4th Grade Science, Tricky Homophones, Greek & Latin Roots).

```markdown
You are an elementary educator creating a spelling curriculum. 
Please generate a comprehensive spelling list in CSV format for:

Grade Level / Topic: [e.g. "4th Grade Essential Spelling Words - Tricky Homophones & Silent Letters"]
Folder Name: [e.g. 4th Grade Master Lists]
Number of Lists: [e.g. 3 lists of 15 words each]

Output Requirements:
1. Provide the output STRICTLY as raw CSV text (NO conversational text or markdown code fences).
2. The first line MUST be:
folder,list_title,word,context_sentence
3. Each word must have a clear, engaging context sentence suitable for elementary students.
4. If a sentence contains commas or quotation marks, wrap the sentence in double quotes.

Example Output:
folder,list_title,word,context_sentence
4th Grade Master Lists,List 1 (Homophones),hear,"I can hear the birds singing outside the window."
4th Grade Master Lists,List 1 (Homophones),here,"Please place your backpack right here by the door."
4th Grade Master Lists,List 1 (Homophones),their,"The students proudly presented their science projects."
4th Grade Master Lists,List 1 (Homophones),there,"Look over there to see the colorful rainbow."
4th Grade Master Lists,List 1 (Homophones),they're,"They're going to the library this afternoon."
```

---

### Prompt 3: Generate Themed Science or Social Studies Vocabulary
> **Use Case**: For weekly science, geography, or history vocabulary tests.

```markdown
You are a teacher creating a subject-specific spelling and vocabulary list.
Please generate a CSV list for:

Subject: [e.g. 4th Grade Earth Science - Weather & Water Cycle]
Folder Name: [e.g. 4th Grade Science Vocabulary]
List Title: [e.g. Weather & Water Cycle]

Output Requirements:
1. Output STRICTLY as raw CSV text without markdown fences or pleasantries.
2. Header format:
folder,list_title,word,context_sentence
3. Provide a clear definition-style or context-rich sentence for every term so elementary students understand how the word is used.
4. Wrap any sentences with internal commas in double quotes.

Example Output:
folder,list_title,word,context_sentence
4th Grade Science Vocabulary,Weather & Water Cycle,evaporation,"Heat from the sun causes evaporation of water from the lake."
4th Grade Science Vocabulary,Weather & Water Cycle,condensation,"Cooling air leads to condensation and the formation of clouds."
4th Grade Science Vocabulary,Weather & Water Cycle,precipitation,"Rain, snow, and hail are all forms of precipitation."
4th Grade Science Vocabulary,Weather & Water Cycle,temperature,"We use a thermometer to measure the air temperature."
```

---

## 📥 How to Import into SpellMaster

1. **Copy the CSV output** generated by the LLM.
2. Open the **Admin Portal** in your browser $\rightarrow$ click **"📥 Import CSV"** (or navigate to `/admin/import`).
3. Choose either:
   - **Upload CSV File**: Save the LLM text as a `.csv` file and drag & drop it.
   - **Direct Paste**: Click the **"Paste CSV Text"** tab and paste the text directly into the box.
4. Click **"Preview & Validate"**:
   - The app will validate your rows and display an interactive table.
   - You can edit any word, folder, list title, or sentence inline before saving.
5. Click **"✅ Commit & Import Lists"**.
6. **Pre-Cache Audio**: Go to **Admin Overview** (`/admin`) $\rightarrow$ Click **"⚡ Pre-Generate All Word Audio"** to synthesize offline HD neural audio files for all new words!
