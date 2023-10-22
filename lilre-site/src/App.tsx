import React, { useState, useRef } from 'react';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import { Button, Alert, Container, Navbar, Form as BForm, Modal, InputGroup, FormControl, Tooltip, Overlay} from 'react-bootstrap';
import { object, string } from 'yup';
import './App.css';

const urlPostSchema = object({
  url: string().required().max(25000).min(6).url().ensure()
})

function App() {
  const [showModal, setShowModal] = useState(false);
  const [shortenedUrl, setShortenedUrl] = useState('');
  const [showToolTip, setShowToolTip] = useState(false);
  const target = useRef(null);

  const closeModal = () => setShowModal(false);
  const openModal = () => setShowModal(true);

  return (
  <div>
    <Navbar expand="lg" className="bg-body-tertiary" bg="dark" data-bs-theme="dark">
      <Container>
        <Navbar.Brand>LilRe - Url Shortener</Navbar.Brand>
      </Container>
    </Navbar>

    <Modal show={showModal} onHide={closeModal}>
      <Modal.Header closeButton>
        <Modal.Title>Shortened Url</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <InputGroup>
        <Button variant="outline-secondary" ref={target} onClick={() => {
          navigator.clipboard.writeText(shortenedUrl); 
          setShowToolTip(true); 
          setTimeout(() => setShowToolTip(false), 800)
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-clipboard" viewBox="0 0 16 16">
            <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
            <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
          </svg>
        </Button>
        <Overlay target={target.current} show={showToolTip} placement='right'>
          {(props) => (
            <Tooltip {...props}>
              Copied to clipboard
            </Tooltip>
          )}
        </Overlay>
        <FormControl type='url' value={ shortenedUrl } readOnly/>
        </InputGroup>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={closeModal}>
            Close
        </Button>
      </Modal.Footer>
    </Modal>

    <Container className='flex-fill'>
      <div className='jumbotron col-md-10 border p-3 m-5'>
        <Formik
          initialValues={{ url: '' }}
          validationSchema={urlPostSchema}
          onSubmit={( values, { setSubmitting } ) => {
            setTimeout(() => {
              const url = values['url']

              const requestOptions = {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'link': url})
              };
              fetch('https://lilre.link/link', requestOptions)
                .then(response => response.json())
                .then(data => {
                  const path = data["path"];
                  setShortenedUrl('https://lilre.link/' + path)
                  openModal();
                })
                .catch(error => {
                  console.error("There was an error!", error);
                })

              setSubmitting(false);
            })
          }}
        >
          {({ errors, touched, isSubmitting }) => (
            <Form>
              <BForm.Group className="mb-3">
                <BForm.Label>Url</BForm.Label>
                <Field type="url" name="url" className="form-control" />
                {errors.url && touched.url ? (
                  <Alert key='info' variant='info' className="mt-2">{ errors.url }</Alert>
                ) : null}
              </BForm.Group>
              <Button variant="primary" type="submit" disabled={ isSubmitting }>Submit</Button>
            </Form>
          )}
        </Formik>
      </div>
    </Container>
  </div>
  );
}

export default App;
