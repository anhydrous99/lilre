import React from 'react';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import { Button, Alert, Container, Navbar, Form as BForm } from 'react-bootstrap';
import { object, string } from 'yup';
import './App.css';

const urlPostSchema = object({
  url: string().required().max(25000).min(6).url().ensure()
})

function App() {
  return (
  <div>
    <Navbar expand="lg" className="bg-body-tertiary" bg="dark" data-bs-theme="dark">
      <Container>
        <Navbar.Brand>LilRe - Url Shortener</Navbar.Brand>
      </Container>
    </Navbar>

    <Container className='flex-fill'>
      <div className='jumbotron col-md-10 border p-3 m-5'>
        <Formik
          initialValues={{ url: '' }}
          validationSchema={urlPostSchema}
          onSubmit={( values, { setSubmitting } ) => {
            console.log(values)
            setSubmitting(false);
          }}
        >
          {({ errors, touched, isSubmitting }) => (
            <Form>
              <BForm.Group className="mb-3">
                <BForm.Label>Url</BForm.Label>
                <Field type="text" name="url" className="form-control" />
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
