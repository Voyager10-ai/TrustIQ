import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyCvI_HshA2KzNdrzqJhbFuakUOvhBN4FM4",
  authDomain: "ai-behavioral-integrity-engine.firebaseapp.com",
  projectId: "ai-behavioral-integrity-engine",
  storageBucket: "ai-behavioral-integrity-engine.appspot.com",
  messagingSenderId: "422300155896",
  appId: "1:422300155896:web:7fa33ccb5fbe26df1d200d",
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();