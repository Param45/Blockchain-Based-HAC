// config/roles.js

// Map addresses to roles for hierarchical access
const ROLES = {
    "0x1111111111111111111111111111111111111111": "Director",
    "0x2222222222222222222222222222222222222222": "Professor1",
    "0x3333333333333333333333333333333333333333": "Professor2",
    "0x4444444444444444444444444444444444444444": "Student1",
    "0x5555555555555555555555555555555555555555": "Student2",
    "0x6666666666666666666666666666666666666666": "Student3"
};

function getRole(address) {
    return ROLES[address.toLowerCase()] || "Unknown";
}

module.exports = {
    ROLES,
    getRole
};
