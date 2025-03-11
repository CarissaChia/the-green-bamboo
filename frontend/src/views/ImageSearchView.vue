<template>
  <NavBar />

  <div class="image-search">
    <h1 class="p-3">Wondering if a drink is worth a try?</h1>
    <p>Scan the drink label to discover more info!</p>

    <div
      class="greybox"
      :class="{ dragging: isDragging }"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <label for="file-upload" class="custom-file-upload">
        <img
          src="@../../../Images/Others/camera.png"
          alt="Camera"
          class="camera-icon"
        />
        Drag an image here or upload a file.
      </label>
      <input id="file-upload" type="file" @change="onFileChange" hidden />

      <div>OR</div>

      <div class="link-section">
        <div class="input-container">
          <input
            type="text"
            placeholder="Paste image link"
            v-model="imageLink"
            class="image-link-input"
          />
          <img
            src="@../../../Images/Others/search.png"
            alt="View Image"
            class="search-icon"
            @click="onShowImage"
          />
        </div>

        <div>
            <input type="checkbox" v-model="isHumanChecked" class="check"/>
            I confirm I am not a robot
        </div>

        <button @click="onSubmitImage" :disabled="!isHumanChecked" class="submit-button">
          Submit for Reverse Image Search
        </button>
      </div>

      <!-- Show/Hide Image Button -->
      <button v-if="uploadedImage" @click="toggleImage" class="toggle-button">
        {{ imagePreview ? "Hide Image ▼" : "Show Image ▼" }}
      </button>

      <!-- Display Image -->
      <div v-if="imagePreview" class="uploaded-image">
        <h4>Uploaded Image:</h4>
        <img
          v-if="uploadedImage"
          :src="uploadedImage"
          alt="Uploaded drink label"
          class="image-preview"
        />
        <p v-else>No image</p>
      </div>
    </div>
  </div>

  <!-- Popup Notification -->
  <div v-if="showPopup" class="popup">
    <p>{{ popupMessage }}</p>
  </div>
</template>

<script>
import NavBar from "@/components/NavBar.vue";

export default {
  name: "ImageSearchView",
  components: { NavBar },
  data() {
    return {
      imageLink: "",
      uploadedImage: "", // Stores the displayed image (uploaded or linked)
      isDragging: false,
      imagePreview: false, // Controls image visibility
      showPopup: false, // Controls popup display
      isHumanChecked: false, // New property to track checkbox state
      apiKey: process.env.VUE_APP_GOOGLE_VISION_API_KEY,
    };
  },
  methods: {
    onFileChange(event) {
      const file = event.target.files[0];
      if (file && this.isValidImageType(file)) {
        const reader = new FileReader();
        reader.onload = () => {
          this.uploadedImage = reader.result;
          this.imagePreview = true;
          this.triggerPopup("Image Uploaded Successfully!");
        };
        reader.readAsDataURL(file);
      } else {
        this.triggerPopup(
          "Invalid file type. Please upload a JPG or PNG image!"
        );
      }
    },

    onDrop(event) {
      event.preventDefault();
      this.isDragging = false;

      const file = event.dataTransfer.files[0];
      if (file && this.isValidImageType(file)) {
        const reader = new FileReader();
        reader.onload = () => {
          this.uploadedImage = reader.result;
          this.triggerPopup("Image Uploaded Successfully!");
        };
        reader.readAsDataURL(file);
      } else {
        this.triggerPopup(
          "Invalid file type. Please upload a JPG or PNG image!"
        );
      }
    },

    isValidImageType(file) {
      const allowedExtensions = ["jpg", "jpeg", "png"];
      const fileExtension = file.name.split(".").pop().toLowerCase();
      return allowedExtensions.includes(fileExtension);
    },

    async onShowImage() {
      if (this.imageLink.trim()) {
        if (!this.isValidUrl(this.imageLink)) {
          this.triggerPopup(
            "Invalid URL format. Please enter a valid image link!"
          );
          return;
        }

        const isValidImage = await this.isImageUrl(this.imageLink);
        if (!isValidImage) {
          this.triggerPopup(
            "URL is not a valid image. Please enter an image URL!"
          );
          return;
        }

        this.uploadedImage = this.imageLink;
        this.imagePreview = true;
        this.triggerPopup("Image link successfully loaded!");
      } else {
        console.error("Invalid image link");
      }
    },

    toggleImage() {
      this.imagePreview = !this.imagePreview;
    },
    isValidUrl(string) {
      try {
        new URL(string);
        return true;
      } catch (error) {
        return false;
      }
    },

    async isImageUrl(url) {
      try {
        const response = await fetch(url, { method: "HEAD" });
        const contentType = response.headers.get("content-type");
        return contentType && contentType.startsWith("image/");
      } catch (error) {
        return false;
      }
    },

    onSubmitImage() {
      
      if (this.uploadedImage || this.imageLink.trim()) {
        const imageToSend = this.uploadedImage || this.imageLink;
        // Call reverse image search and route to results page
        this.reverseImageSearch(imageToSend)
          .then((detectedLogo) => {
            if (detectedLogo) {
              // Navigate to results page with the detected logo in query params
              this.$router.push({
                path: "/imageSearchResults",
                query: { logo: detectedLogo },
              });
            } else {
              console.error("No logo detected");
              this.triggerPopup("We couldn't detect any logo in the image, please search manually or try another image!");
            }
          })
          .catch((error) => console.error("Error in reverse image search:", error));
      } else {
        console.error("No image to submit");
        this.triggerPopup("No image detected, please upload an image or enter a link before submitting!")
      }
    },

    async reverseImageSearch(image) { 
    try {
        let base64Image;

        if (image.startsWith("data:image")) {
            // If it's a base64-encoded image from an upload
            base64Image = image.replace(/^data:image\/(png|jpeg|jpg);base64,/, "");
        } else if (image.startsWith("http")) {
            // If it's a direct image URL, fetch it and convert to base64
            const response = await fetch(image);
            const blob = await response.blob();
            base64Image = await this.convertToBase64(blob);
        } else {
            console.error("Invalid image format.");
            return null;
        }

        const visionApiUrl = `https://vision.googleapis.com/v1/images:annotate?key=${this.apiKey}`;
        
        const visionRequest = {
            requests: [
                {
                    image: { content: base64Image },
                    features: [{ type: "LOGO_DETECTION" }],
                },
            ],
        };

        const visionResponse = await fetch(visionApiUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(visionRequest),
        });

        const visionData = await visionResponse.json();
        console.log("Google Vision API Response:", visionData);

        if (!visionData.responses || !visionData.responses[0].logoAnnotations || visionData.responses[0].logoAnnotations.length === 0) {
            console.error("No logo detected");
            return null;
        }

        const detectedLogo = visionData.responses[0].logoAnnotations[0].description;
        console.log("Detected Logo:", detectedLogo);

        return detectedLogo; // Return detected logo for use in onSubmitImage()
    } catch (error) {
        console.error("Error in reverse image search:", error);
        return null;
    }
},

// Helper function to convert an image blob to base64
async convertToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onload = () => resolve(reader.result.replace(/^data:image\/(png|jpeg|jpg);base64,/, ""));
        reader.onerror = error => reject(error);
    });
},
    // async reverseImageSearch(image) {
    //   let base64Image;

    //     if (image.startsWith("data:image")) {
    //         // If it's a base64-encoded image from an upload
    //         base64Image = image.replace(/^data:image\/(png|jpeg|jpg);base64,/, "");
    //     } else if (image.startsWith("http")) {
    //         // If it's a direct image URL, fetch it and convert to base64
    //         const response = await fetch(image);
    //         const blob = await response.blob();
    //         base64Image = await this.convertToBase64(blob);
    //     } else {
    //         console.error("Invalid image format.");
    //         return null;
    //     }
    //     const visionApiUrl = `https://vision.googleapis.com/v1/images:annotate?key=${this.apiKey}`;
        
    //     const visionRequest = {
    //       requests: [
    //         {
    //           image: { content: base64Image },
    //           features: [{ type: "LOGO_DETECTION" }],
    //         },
    //       ],
    //     };

    //     const visionResponse = await fetch(visionApiUrl, {
    //       method: "POST",
    //       headers: { "Content-Type": "application/json" },
    //       body: JSON.stringify(visionRequest),
    //     });

    //     const visionData = await visionResponse.json();
    //     console.log("Google Vision API Response:", visionData);

    //     if (
    //       !visionData.responses ||
    //       !visionData.responses[0].logoAnnotations ||
    //       visionData.responses[0].logoAnnotations.length === 0
    //     ) {
    //       console.error("No logo detected");
    //       return null;
    //     }

    //     const detectedLogo = visionData.responses[0].logoAnnotations[0].description;
    //     console.log("Detected Logo:", detectedLogo);

    //     return detectedLogo; // Return the detected logo so it can be used in onSubmitImage()

    //   } catch (error) {
    //     console.error("Error in reverse image search:", error);
    //     return null;
    //   }
    // },

    onDragOver(event) {
      event.preventDefault();
      this.isDragging = true;
    },

    onDragLeave() {
      this.isDragging = false;
    },

    triggerPopup(message) {
      this.popupMessage = message;
      this.showPopup = true;
      setTimeout(() => {
        this.showPopup = false;
      }, 3000);
    },
  },
};
</script>

<style scoped>
.image-search {
  text-align: center;
  margin-top: 50px;
}

.greybox {
  width: 90%;
  margin: 50px auto;
  background-color: #f4f4f47d;
  border-radius: 5px;
  display: block;
  text-align: center;
  border: 5px solid #027562;
  padding: 50px 10px;
  /* max-width: 500px; */
}

.upload-section,
.link-section {
  margin: 20px auto;
  width: 80%;
}

.image-search h1,
.image-search p {
  color: #027562;
}

.uploaded-image {
  margin-top: 10px;
}

.custom-file-upload {
  display: inline-block;
  padding: 10px 20px;
  margin: 20px auto;
  cursor: pointer;
  background-color: #f4f4f4;
  border: 2px dashed #ccc;
  text-align: center;
}

.camera-icon {
  width: 24px;
  height: 24px;
  margin-right: 10px;
  vertical-align: middle;
}

.image-preview {
  max-width: 100%;
  height: auto;
  margin-top: 20px;
  border: 2px solid #ccc;
  border-radius: 5px;
}

.dragging {
  background-color: #d9f7e1; /* Light green to indicate drop area is active */
  border-color: #027562;
}

.submit-button {
  margin-top: 20px;
  padding: 12px 24px;
  background-color: #027562;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.3s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.submit-button:hover {
  background-color: #066251;
  transform: translateY(-2px); /* Adds a hover effect to lift the button */
}

.submit-button:active {
  transform: translateY(1px); /* Adds a pressed effect */
}

.submit-button img {
  width: 20px;
  height: 20px;
}

.submit-button span {
  font-size: 18px;
  font-weight: bold;
}

.link-section {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  width: 100%;
}

@media (max-width: 600px) {
  .search-button {
    width: 90%;
    font-size: 14px;
  }
}

/* Popup Style */
.popup {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: #0f0275;
  color: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0);
  align-items: center;
  justify-content: center;
  min-width: 200px;
}

/* Make input bar longer */
.input-container {
  position: relative;
  width: 100%;
  max-width: 500px;
}

.image-link-input {
  flex: 1;
  width: 100%;
  padding: 10px 40px 10px 15px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 16px;
}

.search-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  height: 24px;
  transform: translateY(-50%);
  margin-left: 5px;
  cursor: pointer;
  background-color: rgb(255, 255, 255); /* Opaque background */
}

.toggle-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #027562;
  color: white;
  border: none;
  padding: 12px 16px;
  cursor: pointer;
  border-radius: 25px; /* More rounded for a modern look */
  width: auto; /* Auto width to fit text */
  min-width: 150px; /* Ensures a decent size */
  font-size: clamp(14px, 1.2vw, 16px);
  text-align: center;
  transition: background-color 0.3s, transform 0.2s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.toggle-button:hover {
  background-color: #025c4f;
  transform: scale(1.05);
}

.toggle-button:active {
  background-color: #02473c;
  transform: scale(0.98);
}


.check{
  margin-top: 30px;
}
</style>
