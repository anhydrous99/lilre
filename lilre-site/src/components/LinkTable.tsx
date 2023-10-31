import Table from 'react-bootstrap/Table';


export const LinkTable = () => {
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
            </tbody>
        </Table>
    )
}