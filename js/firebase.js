import { initializeApp } from "https://www.gstatic.com/firebasejs/12.12.1/firebase-app.js";

import {
  getAuth
} from "https://www.gstatic.com/firebasejs/12.12.1/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyCjCaNR3Y1upaAXOQ7A44lc54MJgUmXD0g",
  authDomain: "rushops-7629d.firebaseapp.com",
  projectId: "rushops-7629d",
  storageBucket: "rushops-7629d.firebasestorage.app",
  messagingSenderId: "473114249370",
  appId: "1:473114249370:web:afd788f3e68f8bc5603723"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);