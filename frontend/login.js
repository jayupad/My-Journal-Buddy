function loginUser(username, password) {
    // Endpoint for login
    const endpoint = '/api/auth/login/';
  
    // Create the payload
    const payload = {
      username: username,
      password: password
    };
  
    // Use Fetch API to make the POST request
    fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
      console.log(data); 
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }
  
