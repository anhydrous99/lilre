import Table from 'react-bootstrap/Table';
import {useEffect, useState} from "react";
import {Button} from "react-bootstrap";


interface LinkInterface {
    identity_hash: string;
    created_at: string;
    link: string;
    id: string;
}


let updateTableData = () => {
    const requestOptions = {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    };

    const links_promise: Promise<LinkInterface[]> = fetch('https://lilre.link/userlinks', requestOptions)
        .then(response => response.json())
        .then(data => {
            console.log(data['links'])
            return data['links']
        })
        .catch(error => {
            console.error("There was an error!", error);
        })

    return links_promise
}


export const LinkTable = () => {
    const [links, setLinks] = useState<LinkInterface[] | []>([]);

    useEffect(() => {
        updateTableData().then(
            (data) => {
                setLinks(data)
            }
        )
    }, []);

    return (
        <Table striped bordered hover>
            <thead>
            <tr>
                <th>#</th>
                <th>Short Link</th>
                <th>Long Link</th>
                <th>Delete</th>
            </tr>
            </thead>
            <tbody>
            { links.length? links.map((value, index) => {
                return (
                    <tr>
                        <td>{ index + 1 }</td>
                        <td>https://lilre.link/{ value.id }</td>
                        <td>{ value.link }</td>
                        <td><Button variant="danger" onClick={() => {
                            const requestOptions = {
                                method: 'DELETE',
                                headers: {'Content-Type': 'application/json'}
                            };

                            fetch('https://lilre.link/link/' + value.id, requestOptions)
                                .catch(error => {
                                    console.error("There was an error!", error);
                                })

                            setTimeout(() => {
                                updateTableData().then(
                                    (data) => {
                                        setLinks(data)
                                    }
                                )
                            }, 200)
                        }}>X</Button></td>
                    </tr>
                )
            }) : (<tr>
                <td colSpan={ 4 }>No links have been created.</td>
            </tr>) }
            </tbody>
        </Table>
    )
}