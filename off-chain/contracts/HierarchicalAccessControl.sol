// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title Hierarchical Access Control Registry
/// @notice Stores public keys and versioned encrypted edge labels for an off-chain cryptographic hierarchy.
/// @dev All heavy cryptography happens off-chain. This contract stores bytes and emits events for agents.
contract HierarchicalAccessControl {

    /// @notice Public key published by an entity (address => pubkey bytes)
    mapping(address => bytes) public pubKeys;

    /// @notice EdgeLabel stores the encrypted tuples and metadata for an edge from -> to
    struct EdgeLabel {
        address from;        // publisher
        address to;          // recipient
        bytes enc_pk_to;     // Enc(pk_to, ek_from)  (ECIES-style bytes)
        bytes e_under;       // E(ek_to, ek_from)   (AES-GCM bytes)
        uint64 version;      // version number set by publisher
        uint256 timestamp;   // block timestamp when published
        bool deleted;        // soft-delete flag
    }

    // mapping: from => to => array of versioned EdgeLabel entries
    mapping(address => mapping(address => EdgeLabel[])) private edges;

    /// @notice Emitted when an entity registers or updates its public key
    event KeyRegistered(address indexed who, bytes pubKey, uint256 timestamp);

    /// @notice Emitted when an edge label is published (EdgeAdd)
    event EdgePublished(
        address indexed from,
        address indexed to,
        bytes enc_pk_to,
        bytes e_under,
        uint64 version,
        uint256 timestamp
    );

    /// @notice Emitted when an edge label is soft-deleted
    event EdgeDeleted(address indexed from, address indexed to, uint64 version, uint256 timestamp);

    /// @notice Emitted when a key rotation is announced (publisher changes public key)
    event KeyRotated(address indexed who, bytes newPubKey, uint64 newVersion, uint256 timestamp);

    // -------------------------
    // Key management functions
    // -------------------------

    /// @notice Register or update your public key bytes.
    /// @param pubKey The public key bytes (curve point encoding or other format)
    function registerPublicKey(bytes calldata pubKey) external {
        require(pubKey.length > 0, "pubKey-empty");
        pubKeys[msg.sender] = pubKey;
        emit KeyRegistered(msg.sender, pubKey, block.timestamp);
    }

    /// @notice Convenience getter to check whether a pubkey exists for an address.
    /// @param who address to query
    /// @return exists true if pubKey exists and non-empty
    function hasPubKey(address who) public view returns (bool exists) {
        return pubKeys[who].length > 0;
    }

    // -------------------------
    // Edge publish / delete
    // -------------------------

    /// @notice Publish an EdgeLabel (EdgeAdd). `msg.sender` is the publisher ("from").
    /// @param to Recipient address (the entity whose key is used in enc_pk_to)
    /// @param enc_pk_to Enc(pk_to, ek_from) - bytes from your off-chain crypto engine
    /// @param e_under   E(ek_to, ek_from) - bytes from your off-chain crypto engine
    /// @param version   Version number set by the publisher (increment as you rotate)
    function publishEdge(
        address to,
        bytes calldata enc_pk_to,
        bytes calldata e_under,
        uint64 version
    ) external {
        require(to != address(0), "to-zero");
        require(enc_pk_to.length > 0, "enc_pk_to-empty");
        require(e_under.length > 0, "e_under-empty");
        require(hasPubKey(to), "to-no-pubkey");       // recipient must have published a public key
        require(hasPubKey(msg.sender), "from-no-pubkey"); // publisher should have registered their pubkey (optional but recommended)

        EdgeLabel memory el = EdgeLabel({
            from: msg.sender,
            to: to,
            enc_pk_to: enc_pk_to,
            e_under: e_under,
            version: version,
            timestamp: block.timestamp,
            deleted: false
        });

        edges[msg.sender][to].push(el);

        emit EdgePublished(msg.sender, to, enc_pk_to, e_under, version, block.timestamp);
    }

    /// @notice Mark the latest label of (msg.sender -> to) as deleted (soft delete). Optionally specify version to delete.
    /// Only the original publisher may delete.
    /// @param to Recipient address
    /// @param version Version to mark deleted. If set to `type(uint64).max`, delete the latest version.
    function deleteEdge(address to, uint64 version) external {
        require(to != address(0), "to-zero");
        EdgeLabel[] storage arr = edges[msg.sender][to];
        require(arr.length > 0, "no-edge");

        uint256 idx;
        bool found = false;
        if (version == type(uint64).max) {
            idx = arr.length - 1;
            found = !arr[idx].deleted;
        } else {
            // search for the matching version from the end (most recent first)
            for (uint256 i = arr.length; i > 0; --i) {
                uint256 j = i - 1;
                if (arr[j].version == version) {
                    idx = j;
                    found = !arr[j].deleted;
                    break;
                }
            }
        }
        require(found, "version-not-found-or-already-deleted");

        arr[idx].deleted = true;
        emit EdgeDeleted(msg.sender, to, arr[idx].version, block.timestamp);
    }

    // -------------------------
    // Key rotation helper
    // -------------------------

    /// @notice Rotate your public key and emit KeyRotated event (for off-chain agents to respond).
    /// You should also republish new edge labels after rotating keys as required by your protocol.
    /// @param newPubKey The new public key bytes
    /// @param newVersion A monotonic version number representing this rotation
    function rotateKey(bytes calldata newPubKey, uint64 newVersion) external {
        require(newPubKey.length > 0, "newPubKey-empty");
        pubKeys[msg.sender] = newPubKey;
        emit KeyRotated(msg.sender, newPubKey, newVersion, block.timestamp);
    }

    // -------------------------
    // Read helpers
    // -------------------------

    /// @notice Get the number of versions stored for a given (from -> to) pair.
    function getEdgeCount(address from, address to) external view returns (uint256) {
        return edges[from][to].length;
    }

    /// @notice Get a specific EdgeLabel (by index) for a (from -> to) pair.
    /// @param from Publisher address
    /// @param to Recipient address
    /// @param index Index in the version array (0 = oldest)
    /// @return from_ Publisher address
    /// @return to_ Recipient address
    /// @return enc_pk_to Encrypted pk_to bytes
    /// @return e_under Encrypted ek bytes
    /// @return version Version of the edge
    /// @return timestamp Timestamp of creation
    /// @return deleted Soft-delete flag
    function getEdgeByIndex(address from, address to, uint256 index)
        external
        view
        returns (
            address from_,
            address to_,
            bytes memory enc_pk_to,
            bytes memory e_under,
            uint64 version,
            uint256 timestamp,
            bool deleted
        )
    {
        require(index < edges[from][to].length, "index-oob");
        EdgeLabel storage el = edges[from][to][index];
        return (el.from, el.to, el.enc_pk_to, el.e_under, el.version, el.timestamp, el.deleted);
    }

    /// @notice Get the latest (most recent) EdgeLabel for a (from -> to) pair.
    /// @param from Publisher address
    /// @param to Recipient address
    /// @return from_ Publisher address
    /// @return to_ Recipient address
    /// @return enc_pk_to Encrypted pk_to bytes
    /// @return e_under Encrypted ek bytes
    /// @return version Version of the edge
    /// @return timestamp Timestamp of creation
    /// @return deleted Soft-delete flag
    function getLatestEdge(address from, address to)
        external
        view
        returns (
            address from_,
            address to_,
            bytes memory enc_pk_to,
            bytes memory e_under,
            uint64 version,
            uint256 timestamp,
            bool deleted
        )
    {
        uint256 len = edges[from][to].length;
        require(len > 0, "no-edge");
        EdgeLabel storage el = edges[from][to][len - 1];
        return (el.from, el.to, el.enc_pk_to, el.e_under, el.version, el.timestamp, el.deleted);
    }

    /// @notice Convenience: read the public key for an address.
    function getPubKey(address who) external view returns (bytes memory) {
        return pubKeys[who];
    }
}
