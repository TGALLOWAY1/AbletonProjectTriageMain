Here is the definitive **Master Plan** for your Ableton Triage Assistant. This consolidates every requirement we have discussed into a safe, linear workflow.

---

### **The Master Workflow**

#### **Phase 1: The Deep Scan (Automated Discovery)**
* **Goal:** Index every Ableton project on your system without moving or altering a single file.
* **1.1 Crash-Proof Crawl:** The app scans user-defined locations (e.g., `Music/`, `Desktop/`, `External_Drive/`). It gracefully logs and skips system folders that deny permission, ensuring the scan finishes.
* **1.2 Semantic Decoding:** The scanner reads filenames to extract:
    * **Key & BPM:** Decodes patterns like `Dm_140_Banger.als`.
    * **Intent:** Scans for keywords.
        * *Diamond Tier:* `RENDER`, `FINAL`, `BANGER` (Auto-tags as "Salvage/Review").
        * *Gold Tier:* `MUST USE`, `GOOD DRUMS`, `FIRE` (Adds "🔥" Badge).
* **1.3 Forensic Analysis:**
    * **Sweat Equity:** Calculates "Time Spent" by analyzing the date range and file count in the `Backup/` folder.
    * **Cluster Logic:** Groups multiple versions (`v1`, `v2`, `FINAL`) under a single Project Header to de-clutter the list.
* **1.4 Signal Scoring:** Assigns a 0-100 score to every project based on the data above, sorting your "Best" work to the top.

#### **Phase 2: The Virtual Triage (Decision Making)**
* **Goal:** Review and tag your portfolio. **No files move yet.**
* **2.1 The Dashboard:** You view your projects sorted by "Signal Score."
* **2.2 Instant Preview:** If a `.wav` or `.mp3` export exists in the folder, the app plays it immediately. No need to open Ableton.
* **2.3 The Triage Actions:** You assign one of three tags to every project:
    * **🛑 TRASH:** Projects with no value. (Status: *Pending Archive*)
    * **⚠️ SALVAGE:** Projects with good elements (loops/presets) but the song itself is dead. (Status: *Pending Harvest*)
    * **✅ MUST FINISH:** Your best work. (Status: *Pending Hygiene*)

#### **Phase 3: The Hygiene Loop (Human Work)**
* **Goal:** Process the files to ensure they are safe to move. The app acts as a "To-Do List" manager here.
* **3.1 The "Salvage" Run:**
    * Filter app by **Salvage**.
    * User Action: Open project -> Render loops/save presets to your User Library -> Close.
    * App Action: User marks project as "Harvested."
* **3.2 The "Must Finish" Run:**
    * Filter app by **Must Finish**.
    * User Action: Open project -> **Perform "Collect All and Save"** -> Export a fresh reference mix -> Close.
    * App Action: User marks project as "Ready for Migration."

#### **Phase 4: The Grand Migration (Automated Execution)**
* **Goal:** The physical reorganization of your hard drive. This only runs when you click "Execute."
* **4.1 Dependency Check:** The app verifies that "Must Finish" projects are self-contained (checking XML for external file references).
* **4.2 The Archive Move:**
    * Moves all **Trash** and **Harvested Salvage** project folders to: `[External Drive]/Ableton_Archive/[Date]/`.
* **4.3 The Curated Move:**
    * Moves all **Must Finish** project folders to: `[User Music Folder]/2026_Music/[Genre]/`.
    * *Note:* User selects the Genre tag (e.g., "Dubstep", "House") during the migration prompt.
* **4.4 Cleanup:** Removes the now-empty parent folders from your chaotic source directories.

#### **Phase 5: The Studio Manager (The Finish Line)**
* **Goal:** A simplified "CRM" for finishing your music.
* **5.1 The New View:** The app now points to your `2026_Music` folder.
* **5.2 Production Tags:** You can now tag these active projects with actionable next steps:
    * *Needs Arrangement*
    * *Needs Mixing*
    * *Needs Vocal Recording*
* **5.3 Priority sorting:** Drag-and-drop ordering to plan your studio sessions.

---

**Does this fully capture the vision? If so, I am ready to write the Python script for Phase 1 (The Deep Scan).**