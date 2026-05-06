import { auth } from "./firebase.js";

import {
  createUserWithEmailAndPassword
} from "https://www.gstatic.com/firebasejs/12.12.1/firebase-auth.js";

const registerBtn =
  document.getElementById("registerBtn");

registerBtn.addEventListener("click", async () => {

  const email =
    document.getElementById("email").value;

  const password =
    document.getElementById("password").value;

  try {

    await createUserWithEmailAndPassword(
      auth,
      email,
      password
    );

    window.location.href =
      "/templates/dashboard.html";

  } catch(error) {

    alert(error.message);

  }

});