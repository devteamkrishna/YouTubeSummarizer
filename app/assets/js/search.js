// console.log("📢 JS Loaded");

// document.addEventListener("DOMContentLoaded", () => {
//   const searchBtn = document.getElementById("banner-search");
//   const inputField = document.querySelector(".summarize-search-bar input[type='text']");
//   const loader = document.getElementById("fullscreen-loader");

//   searchBtn.addEventListener("click", async () => {
//     const topic = inputField.value.trim();
//     if (!topic) {
//       alert("Please enter a topic or YouTube URL.");
//       return;
//     }

//     loader.classList.remove("d-none"); // Show loader
//     document.getElementById("videoResults").innerHTML = ""; // Clear old results
//     try {
//       const res = await fetch("/search_videos", {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//           "x-api-key": "secret123"
//         },
//         body: JSON.stringify({ topic })
//       });

//       console.log("📡 Got response:", res);

//       let data;
//       try {
//         data = await res.json();
//         console.log("📦 Parsed JSON:", data);
//       } catch (jsonErr) {
//         throw new Error("Failed to parse JSON response.");
//       }

//       if (res.ok && Array.isArray(data.videos) && data.videos.length > 0) {
//         renderResults(data.videos);
//         console.log("✅ Finished rendering, hiding loader now.");
//       } else {
//         console.warn("⚠️ No videos or bad structure", data);
//         throw new Error("No videos found or invalid response.");
//       }

//     } catch (err) {
//       console.log("🚨 Catch block hit");
//       console.error("❌ Error during fetch/render:", err);
//       alert(err.message || "Something went wrong while fetching videos.");
//     } finally {
//       console.log("🧹 Finally block: hiding loader");
//       loader.classList.add("d-none"); // Always hide loader
//     }

//   });
// });




// function renderResults(videos) {
//   const container = document.getElementById("videoResults");
//   container.innerHTML = ""; // Clear previous results

//   videos.forEach(video => {
//     const summaryPoints = video.summary
//       .split(/\*\*Point\d+\:\*\*/)
//       .filter(p => p.trim())
//       .map(pt => `<li>${pt.trim()}</li>`)
//       .join("");

//     const cardHTML = `
//       <div class="col-md-6 col-lg-4">
//         <div class="summerize-card-box">
//           <div class="card">
//             <iframe width="100%" height="280" src="${video.iframe}" title="${video.title}" frameborder="0"
//               allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
//               referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
//             <div class="card-body px-0 pb-0">
//               <h5 class="card-title">${video.title}</h5>
//               <p class="card-text">${video.channel}</p>
//               <div class="summerize-card-dsc">
//                 <ul>${summaryPoints}</ul>
//               </div>
//               <div class="summerize-card-search d-flex">
//                 <div class="input-group">
//                   <input type="text" class="form-control border-0 ps-0" placeholder="Ask something..." data-videoid="${video.vid_id}" />
//                   <span class="input-group-text border-0 ms-1 chat-submit" style="cursor:pointer;" data-videoid="${video.vid_id}">
//                     <i class="fa-solid fa-comments"></i>
//                   </span>
//                 </div>
//               </div>
//               <div class="chat-response text-sm text-muted mt-2"></div>
//             </div>
//           </div>
//         </div>
//       </div>
//     `;

//     container.insertAdjacentHTML("beforeend", cardHTML);
//   });

//   bindChatEvents();
// }

                                                                                                    
// function bindChatEvents() {
//   const chatButtons = document.querySelectorAll(".chat-submit");

//   chatButtons.forEach(btn => {
//     btn.addEventListener("click", async () => {
//       const videoId = btn.getAttribute("data-videoid");
//       const input = btn.closest(".input-group").querySelector("input");
//       const query = input.value.trim();
//       const responseBox = btn.closest(".card-body").querySelector(".chat-response");

//       if (!query) {
//         responseBox.innerText = "❗ Please enter a question.";
//         return;
//       }

//       responseBox.innerText = "⏳ Getting answer...";

//       try {
//         const res = await fetch("/chat_video", {
//           method: "POST",
//           headers: {
//             "Content-Type": "application/json",
//             "x-api-key": "secret123"
//           },
//           body: JSON.stringify({ video_id: videoId, query })
//         });

//         const data = await res.json();
//         responseBox.innerText = res.ok ? `💬 ${data.answer}` : "❌ Chat failed.";
//       } catch (err) {
//         responseBox.innerText = "❌ Chat error.";
//         console.error("Chat error:", err);
//       }
//     });
//   });
// }


// NEW CODE SNIPPET
console.log("📢 JS Loaded");

document.addEventListener("DOMContentLoaded", () => {
  const searchBtn = document.getElementById("banner-search");
  const inputField = document.querySelector(".summarize-search-bar input[type='text']");
  const loader = document.getElementById("fullscreen-loader");

  searchBtn.addEventListener("click", async () => {
    const topic = inputField.value.trim();
    if (!topic) {
      alert("Please enter a topic or YouTube URL.");
      return;
    }

    const chatSection = document.querySelector(".summarize-video");
    if (chatSection) {
      chatSection.classList.add("d-none");
    }

    loader.classList.remove("d-none"); // Show loader
    document.getElementById("videoResults").innerHTML = ""; // Clear old results
    try {
      const res = await fetch("/search_videos", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": "secret123"
        },
        body: JSON.stringify({ topic })
      });

      console.log("📡 Got response:", res);

      let data;
      try {
        data = await res.json();
        console.log("📦 Parsed JSON:", data);
      } catch (jsonErr) {
        throw new Error("Failed to parse JSON response.");
      }

      if (res.ok && Array.isArray(data.videos) && data.videos.length > 0) {
        renderResults(data.videos);
        console.log("✅ Finished rendering, hiding loader now.");
      } else {
        console.warn("⚠️ No videos or bad structure", data);
        throw new Error("No videos found or invalid response.");
      }

    } catch (err) {
      console.log("🚨 Catch block hit");
      console.error("❌ Error during fetch/render:", err);
      alert(err.message || "Something went wrong while fetching videos.");
    } finally {
      console.log("🧹 Finally block: hiding loader");
      loader.classList.add("d-none"); // Always hide loader
    }

  });
    // ✅ Enable Enter key to trigger the search button
    inputField.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault(); // Prevent form submission or unwanted behavior
        if (searchBtn && !searchBtn.disabled) {
          searchBtn.click();
        }
      }
    });
});


function renderResults(videos) {
  const container = document.getElementById("videoResults");
  container.innerHTML = ""; // Clear previous results

  videos.forEach(video => {
    const summaryPoints = video.summary
      .split(/\*\*Point\d+\:\*\*/)
      .filter(p => p.trim())
      .map(pt => `<li>${pt.trim()}</li>`)
      .join("");

    const cardHTML = `
      <div class="col-md-6 col-lg-4">
        <div class="summerize-card-box">
          <div class="card">
            <iframe width="100%" height="280" src="${video.iframe}" title="${video.title}" frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
            <div class="card-body px-0 pb-0">
              <h5 class="card-title">${video.title}</h5>
              <p class="card-text">${video.channel}</p>
              <div class="summerize-card-dsc">
                <ul>${summaryPoints}</ul>
              </div>
              <div class="text-end mt-2">
                <button class="btn btn-sm btn-outline-primary chat-submit" data-videoid="${video.vid_id}">
                  <i class="fa-solid fa-comments me-1"></i> Ask AI
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    container.insertAdjacentHTML("beforeend", cardHTML);
  });

  bindChatEvents();
}

                                                                                                    
function bindChatEvents() {
  const chatButtons = document.querySelectorAll(".chat-submit");

  chatButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const videoId = btn.getAttribute("data-videoid");
    const card = btn.closest(".card");
    const iframeSrc = card.querySelector("iframe").getAttribute("src");
    const chatInput = document.getElementById("chat-input");

    if (chatInput) {
      // Clone the input to remove all old listeners
      const newChatInput = chatInput.cloneNode(true);
      chatInput.parentNode.replaceChild(newChatInput, chatInput);

      newChatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          const submitBtn = document.getElementById("chat-submit");
          if (submitBtn && !submitBtn.disabled) {
            submitBtn.click();
          }
        }
      });
    }

    // Set the iframe src in the chat tab
    const chatIframe = document.getElementById("chat-iframe");
    if (chatIframe) {
      chatIframe.setAttribute("src", iframeSrc);
    }

    // Store videoId for chat submission
    document.getElementById("chat-submit").setAttribute("data-videoid", videoId);

    // 🔁 Reset chat messages
    const messagesBox = document.getElementById("chat-messages");
    if (messagesBox) {
      messagesBox.innerHTML = `
        <div class="chat-placeholder" id="chat-placeholder">
          💬 Ask anything about this video
        </div>
      `;
    }

    // Clear input value
    const input = document.getElementById("chat-input");
    if (input) {
      input.value = "";
    }

    // Show the chat tab section
    const chatSection = document.querySelector(".summarize-video");
    if (chatSection) {
      chatSection.classList.remove("d-none");
    }

    // 👉 Smooth scroll to chat section
    chatSection.scrollIntoView({ behavior: "smooth", block: "start" });

    // Switch to chat tab
    const chatTab = document.querySelector("#pills-chat-tab");
    if (chatTab) {
      chatTab.click();
    }
  });
});

  // Chat input handling
// Chat input handling
const chatSubmit = document.getElementById("chat-submit");

if (chatSubmit) {
  // Remove any previous listener to prevent duplicates
  chatSubmit.replaceWith(chatSubmit.cloneNode(true));

  const freshChatSubmit = document.getElementById("chat-submit");

  freshChatSubmit.addEventListener("click", async () => {
    const videoId = freshChatSubmit.getAttribute("data-videoid");
    const input = document.getElementById("chat-input");
    const query = input.value.trim();
    const messagesBox = document.getElementById("chat-messages");
    const placeholder = document.getElementById("chat-placeholder");

    if (!query) {
      appendMessage("You", "❗ Please enter a question.", "user", messagesBox);
      return;
    }


    // Disable button + show loader
    chatSubmit.disabled = true;
    const spinner = chatSubmit.querySelector(".spinner-border");
    const btnText = chatSubmit.querySelector(".btn-text");
    if (spinner && btnText) {
      spinner.classList.remove("d-none");
      btnText.textContent = "Asking...";
    }

    if (placeholder) placeholder.remove();

    appendMessage("You", query, "user", messagesBox);
    const loadingMessage = appendMessage("AI", "⏳ Getting answer...", "ai", messagesBox);

    input.value = "";

    try {
      const res = await fetch("/chat_video", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": "secret123"
        },
        body: JSON.stringify({ video_id: videoId, query })
      });

      const data = await res.json();
      loadingMessage.innerText = res.ok ? `AI: 💬 ${data.answer}` : "AI: ❌ Chat failed.";
    } catch (err) {
      loadingMessage.innerText = "AI: ❌ Chat error.";
      console.error("Chat error:", err);
    }
      // Re-enable button + hide loader
    chatSubmit.disabled = false;
    if (spinner && btnText) {
      spinner.classList.add("d-none");
      btnText.textContent = "Ask";
    }

    messagesBox.scrollTop = messagesBox.scrollHeight;
  });
}

  function appendMessage(sender, text, type, container) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("chat-message", type);
    msgDiv.innerText = `${sender}: ${text}`;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    return msgDiv; // Return reference to modify later
  }
}
