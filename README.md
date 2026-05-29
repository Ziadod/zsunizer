# zsu!nizer
**osu! Replay Humanizer & Editor**

An open-source desktop application built with Python that allows users to modify osu! replay files (`.osr`). With one click, you can change the player's name, toggle active mods, and inject human-like cursor movements into robotic or perfectly aimed replays.

I originally created this tool as a fun way to prank my friends into thinking I had become an absolute osu! god overnight. It works so well that I decided to polish it up and release it open-source!

---

### ⚠️ Disclaimer
**This tool is created strictly for educational purposes, offline testing, and experimental replay editing.** It is **NOT** meant to be used for cheating, submitting fraudulent scores on official osu! servers (Bancho), or ruining the competitive integrity of the game. Please respect the game's rules. You are solely responsible for how you use this software.

---

### 🛠️ Features
* **One-Click Humanizer:** Adjust the 4 independent Humanize sliders (Sloppy Aim, Hand Shake, Idle Wandering, and Lazy Tracking) to automatically add natural wrist-sway, slider-cheesing, and cursor jitter throughout the entire replay.
* **Smart Beatmap Sync:** Optionally upload the `.osu` or `.osz` file so the app knows exactly when to apply slider logic vs jump logic!
* **Mod Editor:** Toggle active gameplay mods (EZ, HR, DT, HD, etc.) exactly like the in-game interface.
* **Name Changer:** Easily overwrite the player name stored inside the replay file.

---

### 🚀 The "Auto-to-Human" Tutorial
If you want to use this tool to its full potential (like I did for the prank!), here is the best way to get a perfectly humanized replay:

1. Open osu! and play the beatmap you want, but **turn on the Auto (AT) mod**.
    * **CRITICAL:** *You must also activate any other gameplay-altering mods you want (like HR, DT, or EZ) BEFORE playing the map! If you play the map normally but enable Hard Rock inside the zsu!nizer app later, your cursor will be clicking the air because the circles were not flipped during the actual gameplay.*
2. Let the Auto-player finish the map with a perfect score.
3. Save the replay locally by pressing `F2` at the results screen.
4. Open **zsu!nizer** and load that `.osr` file.
5. *(Optional but recommended)* Load the beatmap (`.osu` or `.osz`) so the app can perfectly sync the slider logic.
6. Change the "Player Name" to your username.
7. In the Mod section, **turn off the Auto (AT) mod** and replace it with whatever you want (like Relax (RX), Hidden (HD), or nothing at all!).
8. Adjust your 4 "Humanize" sliders (or just leave them at their defaults).
9. Click **Convert & Save** and drag the new file back into osu! to watch your "gameplay"!

---

### 🤝 Contributing & Improvements
This tool is a work in progress and highly welcomes community contributions! I am specifically looking for developers who can help with:
* Improving the core **humanizing math and mechanics**.
* Making the cursor movements more natural **during pauses and breaks** between notes.
* General performance optimizations or bug fixes.

If you want to help make it better:
1. Fork the repository.
2. Make your changes or optimizations.
3. Open a Pull Request.

Any help is greatly appreciated! 

---

### 📝 Credits
* Developed and created by **Ziadod**.
