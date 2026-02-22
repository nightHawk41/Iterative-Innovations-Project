// This is the main React component. You can edit this file to add more components and functionality to your frontend.
// Definitions:
// - App: The main React component that will be rendered in the browser. 
//          You can add more components and functionality to this file as needed.
// - useState: A React hook that allows you to add state to your functional components.
//            For example, you can use useState to store data fetched from the backend and display it in the UI.
// - useEffect: A React hook that allows you to perform side effects in your functional components, such as fetching data from an API. 
//            For example, you can use useEffect to fetch data from the Flask backend when the component mounts and update the state with the fetched data.           

import React, {useState, useEffect} from "react";

function App() {

    const [data, setData] = useState([{}]);

    useEffect(() => {
        fetch("/test").then(
            res => res.json()
        ).then(
            data => {
                setData(data);
                console.log(data);
            }
        )
    }, [])

    return (
        <div>
            
            {(typeof data.message === 'undefined') ? (
                <p>Loading...</p>
            ) : (
                data.message.map((word, index) => <p key={index}>{word}</p>)
            )}

        </div>
    );
}

export default App;