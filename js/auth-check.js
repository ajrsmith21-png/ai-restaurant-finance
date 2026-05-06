import { auth } from "./firebase.js";

import {
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/12.12.1/firebase-auth.js";

onAuthStateChanged(auth, (user) => {

  if (!user) {

    window.location.href =
      "/templates/login.html";

    return;
  }

  console.log(
    "Authenticated:",
    user.email
  );

});