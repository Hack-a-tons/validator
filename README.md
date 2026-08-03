# 🛡️ PRE-GEN detect: Visual Jailbreak Detection for AI Video

*Built for the [Hack the Video Agent Context Graph](https://luma.com/hack-video-agent-context-graph-jul30-2026) Hackathon (July 30, 2026).*

## ⚠️ The Problem: The "Visual Jailbreak"
Current AI video generators have a massive loophole. If a user prompts for a protected subject by name, the generation is blocked by standard text filters. However, if the user inputs a highly detailed physical description of that person without using their name, the system happily generates the video. 

This exposes platform operators to severe IP, copyright, and licensing liabilities, as the generated content still visually violates the protected likeness.

## 💡 The Solution
**PRE-GEN detect** is an independent service that detects and blocks these visual jailbreaks. Instead of relying solely on the user's initial text prompt, PRE-GEN detect analyzes the *actual generated visual output* and compares it against protected subject registries before it can be distributed.

### The Ecosystem
This demo integrates with the following platforms to simulate a real-world pipeline:
*   **[Prampta.com](https://prampta.com):** The source of truth for license issues, IP protection, and subject validation rules.
*   **[Buddian.com](https://buddian.com):** The AI video generation platform where the synthesized media is created.
*   **[validator.prampta.com](https://validator.prampta.com):** Standalone demo. Enter video URL and character to search for.

## ⚙️ How It Works (The Demo Flow)
The standalone UI accepts two simple inputs:
1.  **Video URL:** A link to a generated video from Buddian (e.g., `https://buddian.com/app/video?id=241`). The app automatically parses the direct `.mp4` storage link.
2.  **Protected Description:** The text description of the protected subject registered in Prampta.

**The Pipeline:**
1.  **Extraction:** The service safely extracts the raw MP4 from Buddian.
2.  **Visual Analysis (TwelveLabs):** TwelveLabs ingests the video and generates a highly detailed physical description of the primary subject visible on screen.
3.  **Arbitration (OpenAI):** OpenAI acts as the final judge, comparing the TwelveLabs visual extraction against the Prampta protected description.
4.  **Verdict:** 
    *   🔴 **DECLINE:** The visual subject matches the protected description (Jailbreak caught).
    *   🟢 **APPROVE:** The visual subject is definitively different from the protected description.

## 🛠️ Tech Stack
*   **TwelveLabs:** Multimodal video understanding and visual feature extraction.
*   **OpenAI:** Logical reasoning and entity comparison.
*   **Python:** Lightweight routing and UI generation.
