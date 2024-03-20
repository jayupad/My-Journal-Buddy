function registerUser(username, password, email) {
    // Endpoint for registration
    const endpoint = '/api/auth/register/';
  
    // Create the payload
    const payload = {
      username: username,
      password: password,
      email: email
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
      console.log(data); // Handle the response data
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }