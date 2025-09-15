// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyB5Cmw4Xve0F8trCGyr8ddn4Hpw50DzsdA",
  authDomain: "hr-procedural-app.firebaseapp.com",
  projectId: "hr-procedural-app",
  storageBucket: "hr-procedural-app.appspot.com", // ← 修正済み
  messagingSenderId: "281349637785",
  appId: "1:281349637785:web:20989ba2a65fe7e7cc1a08",
  measurementId: "G-GEXEDRKSR7"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

export { app, analytics };